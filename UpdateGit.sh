cd /home/pi/PegasusLogs

echo "!====attempting add:====!\n"
git add /home/pi/PegasusLogs/*

echo "\n!====attempting commit====!\n"
git commit -m 'Added Entries to log'

echo "\n!====attempting push====!\n"
sudo git push origin master

