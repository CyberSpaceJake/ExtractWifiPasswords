import subprocess
import os
import re
import csv
from collections import namedtuple
import configparser

# returns list of SSIDs in a Windows device
def get_windows_ssids():
    output = subprocess.check_output("netsh wlan show profiles").decode()
    ssids = []
    profiles = re.findall(r"All User Profile\s(.*)", output)
    for profile in profiles:
        ssid = profile.strip().strip(":").strip()
        ssids.append(ssid)
    return ssids

# extract saved wifi passwords in Windows for each SSID
def get_wifi_passwords_windows(verbose=1):
    ssids = get_windows_ssids()
    Profile = namedtuple("Profile", ["ssid", "ciphers", "key"])
    profiles = []
    for ssid in ssids:
        ssid_details = subprocess.check_output(f"""netsh wlan show profile "{ssid}" key=clear""").decode()
        ciphers = re.findall(r"Cipher\s(.*)", ssid_details)
        ciphers = "/".join([c.strip().strip(":").strip() for c in ciphers])
        key = re.findall(r"Key Content\s(.*)", ssid_details)
        try:
            key = key[0].strip().strip(":").strip()
        except IndexError:
            key = "None"
        profile = Profile(ssid=ssid, ciphers=ciphers, key=key)
        if verbose >= 1:
            print_windows_profile(profile)
        profiles.append(profile)
    return profiles

def print_windows_profile(profile):
    print(f"{profile.ssid:25}{profile.ciphers:15}{profile.key:50}")

# print all extracted SSIDs and Keys on Windows
def print_windows_profiles(verbose):
    print("SSID                     CIPHER(S)      KEY")
    print("-"*50)
    profiles = get_wifi_passwords_windows(verbose)
    return profiles

# Extract SSIDs and passwords in Linux
def get_linux_saved_wifi_passwords(verbose=1):   
    network_connections_path = "/etc/NetworkManager/system-connections/"
    fields = ["ssid", "auth-alg", "key-mgmt", "psk"]
    Profile = namedtuple("Profile", [f.replace("-", "_") for f in fields])
    profiles = []
    for file in os.listdir(network_connections_path):
        data = { k.replace("-", "_"): None for k in fields }
        config = configparser.ConfigParser()
        config.read(os.path.join(network_connections_path, file))
        for _, section in config.items():
            for k, v in section.items():
                if k in fields:
                    data[k.replace("-", "_")] = v
        profile = Profile(**data)
        if verbose >= 1:
            print_linux_profile(profile)
        profiles.append(profile)
    return profiles

def print_linux_profile(profile):
    print(f"{str(profile.ssid):25}{str(profile.auth_alg):5}{str(profile.key_mgmt):10}{str(profile.psk):50}")

# Prints all extracted SSIDs along with Key (PSK) on Linux
def print_linux_profiles(verbose):
    print("SSID                     AUTH KEY-MGMT  PSK")
    print("-"*50)
    profiles = get_linux_saved_wifi_passwords(verbose)
    return profiles

# call windows or linux function based on OS
def print_profiles(verbose=1):
    if os.name == "nt":
        profiles = print_windows_profiles(verbose)
    elif os.name == "posix":
        profiles = print_linux_profiles(verbose)
    else:
        raise NotImplementedError("Code only works for either Linux or Windows")
    
    # Ask the user if they want to save the data to a CSV file
    save_option = input("Would you like to save the profiles to a CSV file? (yes/no): ").strip().lower()
    if save_option == "yes":
        output_to_csv(profiles)

# Function to output the profiles to a CSV file
def output_to_csv(profiles):
    # Prompt for the CSV file name
    filename = input("Enter the filename (without extension): ") + ".csv"
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["SSID", "CIPHER(S)", "KEY"])
        for profile in profiles:
            writer.writerow([profile.ssid, profile.ciphers, profile.key])
    
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    print_profiles()
