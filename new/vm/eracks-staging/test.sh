# test function to send tgram msg

send_telegram() {
  m="$(hostname -s)_$1"
  wget -O ~/$m "https://api.telegram.org/bot827690020:AAH4_YiCp9W5KEE1hxMMQfh1UXAG8D4ENoE/sendMessage?chat_id=116010224&text=$m"
}

send_telegram is_up!

