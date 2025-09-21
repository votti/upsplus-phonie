#!/bin/bash
# UPS Plus installation script.

# initializing init-functions.
. /lib/lsb/init-functions
sudo raspi-config nonint do_i2c 0

# check if the network is working properly.
log_action_msg "Welcome to 52Pi Technology UPS Plus auto-install Program!"
log_action_msg "More information please visit here:"
log_action_msg "-----------------------------------------------------"
log_action_msg "https://wiki.52pi.com/index.php/UPS_Plus_SKU:_EP-0136"
log_action_msg "-----------------------------------------------------"
log_action_msg "Start the configuration environment check..."
ping_result=`ping -c 4 www.github.com &> /dev/null` 
if [[ $ping_result -ne 0 ]]; then
	log_failure_msg "Network is not available!"
	log_warning_msg "Please check the network configuration and try again!"
else
	log_success_msg "Network status is ok..."
fi

# Package check and installation
install_pkgs()
{
	`sudo apt-get -qq update`
	`sudo apt-get -y -qq install sudo git i2c-tools`
}

log_action_msg "Start the software check..."
pkgs=`dpkg -l | awk '{print $2}' | egrep ^git$`
if [[ $pkgs = 'git' ]]; then
	log_success_msg "git has been installed."
else
	log_action_msg "Installing git package..."
	install_pkgs
	if [[ $? -eq 0 ]]; then 
	   log_success_msg "Package installation successfully."
	else
	   log_failure_msg "Package installation is failed,please install git package manually or check the repository"
	fi
fi	

# create python virtual environment
python3 -m venv $HOME/bin/upsplus/.venv
source $HOME/bin/upsplus/.venv/bin/activate

# install pi-ina219 library.
log_action_msg "Installing pi-ina219 library..."
python3 -m pip install pi-ina219
if [[ $? -eq 0 ]]; then
   log_success_msg "pi-ina219 installation successful."
else
   log_failure_msg "pi-ina219 installation failed!"
   log_warning_msg "Please install it by manual: python3 -m pip install pi-ina219"
fi

# install smbus2 library.
log_action_msg "Installing smbus2 library..."
python3 -m pip install smbus2
if [[ $? -eq 0 ]]; then
        log_success_msg "smbus2 installation successful."
else
    log_failure_msg "smbus2 installation failed!"
    log_warning_msg "Please install it by manual: python3 -m pip install smbus2"
fi

# install requests library.
log_action_msg "Installing requests library..."
python3 -m pip install requests
if [[ $? -eq 0 ]]; then
        log_success_msg "requests installation successful."
else
    log_failure_msg "requests installation failed!"
    log_warning_msg "Please install it by manual: python3 -m pip install requests"
fi

# TODO: Create daemon service or crontab by creating python scripts. 
# create bin folder and create python script to detect UPS's status.
log_action_msg "create $HOME/bin directory..."
/bin/mkdir -p $HOME/bin/upsplus
export PATH=$PATH:$HOME/bin/upsplus
cp upsplus.py $HOME/bin/upsplus/upsplus.py 
# Create python script.
log_action_msg "Create python3 script in location: $HOME/bin/upsplus.py Successful"
# Upload the battery status to the data platform for subsequent technical support services 
# Add service 
log_action_msg "Add service for batteryups list."
# This service runs under the current user, but on startup before user logins
# Thus set the current username as user

envsubst < upsplus.service | sudo tee /etc/systemd/system/upsplus.service
sudo cp upsplus.timer /etc/systemd/system/

sudo systemctl start upsplus.service
systemctl status upsplus.service
