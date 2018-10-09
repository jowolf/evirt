echo tail -f /var/log/cloud-init-output.log >> /home/$user/.bash_history
echo less /var/log/cloud-init-output.log >> /home/$user/.bash_history
echo less /var/log/cloud-init.log >> /home/$user/.bash_history
echo sudo netstat -antp >> /home/$user/.bash_history
