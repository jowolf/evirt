cat >x <<EOF
# JJW - Restore some ssh defaults overridden by Debian (Poor judgement - breaks pw auth!)
UsePAM no
Printmotd yes
X11Forwarding no
PasswordAuthentication yes
ChallengeResponseAuthentication yes
# JJW: Note that counterintuitively, first-encountered options override later-specced ones - 
# unlike most other software configs - that's why this section is at the TOP of the file.
# see the ssh and sshd_config manpages for the gory details. j

EOF

cat x /etc/ssh/sshd_config >y

sudo cp y /etc/ssh/sshd_config
sudo service sshd restart
