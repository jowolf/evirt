/*
 * Copyright (c) 2004 Novell, Inc.
 * Copyright (c) 2005 Manuel Amador <rudd-o@rudd-o.com>
 * Copyright (c) 2009 Forest Bond <forest@alittletooquiet.net>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

#include <Python.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/select.h>
#include <sys/inotify.h>
#include <linux/types.h>
#include <linux/limits.h>


#define MAX_PENDING_PAUSE_COUNT    5
#define PENDING_PAUSE_MICROSECONDS 2000
#define PENDING_THRESHOLD(qsize)   ((qsize) >> 1)

#define EVENT_SIZE (sizeof (struct inotify_event))
#define BUF_LEN (1024 * (EVENT_SIZE + 16))


static PyObject * inotifyx_init(PyObject *self, PyObject *args) {
    int fd;

    fd = inotify_init();

    if(fd < 0) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }
    return Py_BuildValue("i", fd);
}


static PyObject * inotifyx_add_watch(PyObject *self, PyObject *args) {
    int fd;
    char *path;
    int watch_descriptor;
    uint32_t mask;

    mask = IN_ALL_EVENTS;

    if(! PyArg_ParseTuple(args, "is|i", &fd, &path, &mask)) {
        return NULL;
    }

    watch_descriptor = inotify_add_watch(fd, (const char *)path, mask);

    if(watch_descriptor < 0) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }
    return Py_BuildValue("i", watch_descriptor);
}


static PyObject * inotifyx_rm_watch(PyObject *self, PyObject *args) {
    int fd;
    int watch_descriptor;
    int retvalue;

    if(! PyArg_ParseTuple(args, "ii", &fd, &watch_descriptor)) {
        return NULL;
    }
    retvalue = inotify_rm_watch(fd, watch_descriptor);
    if(retvalue < 0) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }
    return Py_BuildValue("i", retvalue);
}


static PyObject * inotifyx_get_events(PyObject *self, PyObject *args) {
    int fd;

    static char buf[BUF_LEN];
    int i;
    int len;

    float timeout_arg;

    struct timeval timeout;
    void *ptimeout;

    struct inotify_event *event;

    fd_set read_fds;
    int select_retval;

    timeout_arg = -1.0;
    if(! PyArg_ParseTuple(args, "i|f", &fd, &timeout_arg)) {
        return NULL;
    }

    if(timeout_arg < 0.0) {
        ptimeout = NULL;
    } else {
        timeout.tv_sec = (int)timeout_arg;
        timeout.tv_usec = (int)(1000000.0 * (timeout_arg - (float)((int) timeout_arg)));
        ptimeout = &timeout;
    }

    FD_ZERO(&read_fds);
    FD_SET(fd, &read_fds);

    select_retval = select(fd + 1, &read_fds, NULL, NULL, ptimeout);

    if(select_retval == 0) {
        // Timed out.
        return PyList_New(0);
    } else if(select_retval < 0) {
        PyErr_SetFromErrno(PyExc_IOError);
        return NULL;
    }

    PyObject* retvalue = PyList_New(0);

    timeout.tv_sec = 0;
    timeout.tv_usec = 0;
    ptimeout = &timeout;

    do {
        len = read(fd, buf, BUF_LEN);

        if(len < 0) {
            PyErr_SetFromErrno(PyExc_IOError);
            return NULL;
        } else if(len == 0) {
            PyErr_SetString(PyExc_IOError, "event buffer too small");
            return NULL;
        }

        i = 0;
        while(i < len) {
            event = (struct inotify_event *)(& buf[i]);

            PyObject* value = NULL;
            if(event->name[0] != '\0') {
                value = Py_BuildValue(
                  "iiis",
                  event->wd,
                  event->mask,
                  event->cookie,
                  event->name
                );
            } else {
                value = Py_BuildValue(
                  "iiiO",
                  event->wd,
                  event->mask,
                  event->cookie,
                  Py_None
                );
            }
            if(PyList_Append(retvalue, value) == -1) {
                return NULL;
            }

            i += EVENT_SIZE + event->len;
        }

        FD_ZERO(&read_fds);
        FD_SET(fd, &read_fds);
    } while(select(fd + 1, &read_fds, NULL, NULL, ptimeout) > 0);

    return retvalue;
}


static PyMethodDef InotifyMethods[] = {
  {
    "init",
    inotifyx_init,
    METH_VARARGS,
    (
      "init()\n\n"
      "Initialize an inotify instance and return the associated file\n"
      "descriptor.  The file descriptor should be closed via os.close\n"
      "after it is no longer needed."
    )
  },
  {
    "add_watch",
    inotifyx_add_watch,
    METH_VARARGS,
    (
      "add_watch(fd, path[, mask])\n\n"
      "Add a watch for path and return the watch descriptor.\n"
      "fd should be the file descriptor returned by init.\n"
      "If left unspecified, mask defaults to IN_ALL_EVENTS.\n"
      "See the inotify documentation for details."
    )
  },
  {
    "rm_watch",
    inotifyx_rm_watch,
    METH_VARARGS,
    (
      "rm_watch(fd, wd)\n\n"
      "Remove the watch associated with watch descriptor wd.\n"
      "fd should be the file descriptor returned by init.\n"
    )
  },
  {
    "get_events",
    inotifyx_get_events,
    METH_VARARGS,
    "get_events(fd[, timeout])\n\n"
    "Read events from inotify and return a list of tuples "
    "(wd, mask, cookie, name).\n"
    "The name field is None if no name is associated with the inotify event.\n"
    "Timeout specifies a timeout in seconds (as an integer or float).\n"
    "If left unspecified, there is no timeout and get_events will block\n"
    "indefinitely.  If timeout is zero, get_events will not block."
  },
  {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC init_inotifyx(void) {
    PyObject* module = Py_InitModule3(
      "_inotifyx",
      InotifyMethods,
      (
        "Low-level interface to inotify.  Do not use this module directly.\n"
        "Instead, use the inotifyx module."
      )
    );
    
    PyModule_AddIntConstant(module, "IN_ACCESS", IN_ACCESS);
    PyModule_AddIntConstant(module, "IN_MODIFY", IN_MODIFY);
    PyModule_AddIntConstant(module, "IN_ATTRIB", IN_ATTRIB);
    PyModule_AddIntConstant(module, "IN_CLOSE_WRITE", IN_CLOSE_WRITE);
    PyModule_AddIntConstant(module, "IN_CLOSE_NOWRITE", IN_CLOSE_NOWRITE);
    PyModule_AddIntConstant(module, "IN_CLOSE", IN_CLOSE);
    PyModule_AddIntConstant(module, "IN_OPEN", IN_OPEN);
    PyModule_AddIntConstant(module, "IN_MOVED_FROM", IN_MOVED_FROM);
    PyModule_AddIntConstant(module, "IN_MOVED_TO", IN_MOVED_TO);
    PyModule_AddIntConstant(module, "IN_MOVE", IN_MOVE);
    PyModule_AddIntConstant(module, "IN_CREATE", IN_CREATE);
    PyModule_AddIntConstant(module, "IN_DELETE", IN_DELETE);
    PyModule_AddIntConstant(module, "IN_DELETE_SELF", IN_DELETE_SELF);
    PyModule_AddIntConstant(module, "IN_MOVE_SELF", IN_MOVE_SELF);
    PyModule_AddIntConstant(module, "IN_UNMOUNT", IN_UNMOUNT);
    PyModule_AddIntConstant(module, "IN_Q_OVERFLOW", IN_Q_OVERFLOW);
    PyModule_AddIntConstant(module, "IN_IGNORED", IN_IGNORED);
    PyModule_AddIntConstant(module, "IN_ONLYDIR", IN_ONLYDIR);
    PyModule_AddIntConstant(module, "IN_DONT_FOLLOW", IN_DONT_FOLLOW);
    PyModule_AddIntConstant(module, "IN_MASK_ADD", IN_MASK_ADD);
    PyModule_AddIntConstant(module, "IN_ISDIR", IN_ISDIR);
    PyModule_AddIntConstant(module, "IN_ONESHOT", IN_ONESHOT);
    PyModule_AddIntConstant(module, "IN_ALL_EVENTS", IN_ALL_EVENTS);
}
