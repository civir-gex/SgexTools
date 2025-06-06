#!/bin/bash

if ! [[ "12 15" == *"$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1)"* ]];
then
    echo "SLES $(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1) is not currently supported.";
    exit;
fi

# Import the GPG key
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
# Download the package to configure the Microsoft repo
curl -sSL -O https://packages.microsoft.com/config/sles/$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1)/packages-microsoft-prod.rpm
# Install the package
sudo zypper install packages-microsoft-prod.rpm
# Delete the file
rm packages-microsoft-prod.rpm

sudo zypper update
sudo ACCEPT_EULA=Y zypper install -y msodbcsql18
# optional: for bcp and sqlcmd
sudo ACCEPT_EULA=Y zypper install -y mssql-tools18
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
# optional: for unixODBC development headers
sudo zypper install -y unixODBC-devel