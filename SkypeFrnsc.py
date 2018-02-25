import sys
import os
import datetime
import sqlite3 as lite
import pandas as pd

import logging
import argparse

def create_logger(verbose):
    form = '%(levelname)s: %(message)s'
    if verbose is None:
        logging.basicConfig(format='%(message)s', level=logging.CRITICAL)
    if verbose == 1:
        logging.basicConfig(format=form, level=logging.ERROR)
    if verbose == 2:
        logging.basicConfig(format=form, level=logging.WARNING)
    if verbose == 3:
        logging.basicConfig(format=form, level=logging.DEBUG)


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='count')
    args = parser.parse_args()
    return args

def decodeXML(text):
    text = text.replace("&amp;apos;", "\'")
    text = text.replace("&apos;", "\'")
    text = text.replace("&quot;", "\"")
    return text

def save_data(data, cat):
    fileName = _NAME + cat
    with open(fileName,'wb') as f:
        f.write(data.encode('utf-8'))

def get_contacts(cur):
    toFile = ""
    for row in cur.execute('SELECT skypename FROM Contacts'):
        toFile += row[0] + "\n"
    return toFile

def show_contacts(cur):
    contacts = get_contacts(cur)
    print(contacts)
    choice = input("Do you want to save contact list ? (y/n) : ")
    if choice == 'y':
        save_data(contacts, "_contacts")

def get_conv(cur, contact):
    date = []
    author = []
    text = []
    for row in cur.execute('SELECT * FROM Messages WHERE author=? \
    OR dialog_partner=?', (contact, contact)):
        date.append(row[9])
        text.append(decodeXML(row[17]))
        author.append(row[4])
    tab = pd.DataFrame({'Date':date, 'Author':author, 'Text':text})
    tab = tab.sort_values(by=['Date'])

    conv = "Conversation with " + contact + " :" + "\n\n"
    for i in range(1,len(tab)):
        author = tab.iloc[i][0]
        date = datetime.datetime.fromtimestamp(tab.iloc[i][1]).strftime('[%Y/%m/%d %H:%M:%S]')
        text = tab.iloc[i][2]
        row = date + " " + author + ": " + text + "\n";
        conv += row
    return conv

def conv_from_cont(cur):
    print("\n" + get_contacts(cur))
    contact = input("Enter contact name : ")
    conv = get_conv(cur, contact)
    print(conv)
    choice = input("Do you want to save this conversation ? (y/n) : ")
    if choice == 'y':
        save_data(conv, "_conv_" + contact)

def account_infos(cur):
    toFile = ""
    for row in cur.execute('SELECT * FROM Accounts'):
        for i in range(len(row)):
            toFile += ("\nInfos about " + _NAME + ":")
            toFile += ("\nSkype name : " + row[37])
            toFile += ("\nNickname : " + row[39] if row[39] is not None else "")
            toFile += ("\nGender : " + "Male" if row[41] == 0 else "Female")
            toFile += ("\nCountry code : " + row[43] if row[43] is not None else "")
            toFile += ("\nProvince : " + row[44] if row[44] is not None else "")
            toFile += ("\nCity : " + row[45] if row[45] is not None else "")
            toFile += ("\nPost code : " + str(row[60]))
            toFile += ("\nIp country : " + row[62])
            toFile += ("\nPhone : " + row[46] if row[46] is not None else "") # +47 48
            toFile += ("\nEmail : " + row[49])
            toFile += ("\nHomepage : " + row[50] if row[50] is not None else "")
            toFile += ("\nSignature : " + row[51] if row[51] is not None else "")
            if row[52]:
                toFile += ("\nLast profil modification : " + datetime.datetime.fromtimestamp(row[52]).strftime('%Y/%m/%d %H:%M:%S'))
            toFile += "\n"
            break
    print(toFile)
    choice = input("Do you want to save this profil infos ? (y/n) :")
    if choice == 'y':
        save_data(toFile, "_infos")
    return toFile

def calls_list(cur):
    calls = ""
    for row in cur.execute('SELECT * FROM Calls'):
        calls += "host = " + row[6] + " | dest = " + row[39] + " | time = "
        + row[8] if row[8] > 0 else ""
        calls += "\n"
    print(calls)
    choice = input("Do you want to save calls list ? (y/n) : ")
    if choice == 'y':
        save_data(calls, "_calls")
    return calls

def save_all(cur):
    datas = account_infos(cur) + "\n\n\n 1 -------\n"
    datas += get_contacts(cur) + "\n\n\n 2 --------\n"
    datas += "\n\n 3 -------\n"
    for row in cur.execute('SELECT * FROM Contacts'):
        datas += "\t\t" + get_conv(cur, row[3]) + "\n\n"
    datas += calls_list(cur)
    choice = input("Do you want to save all datas ? (y/n) :")
    if choice == 'y':
        save_data(datas, "_datas")

args = create_parser()
create_logger(args.verbose)

print("Finding Skype accounts...\n")
cmd = os.popen("find /root/.Skype/*/main.db")
r = cmd.read()
paths = r.split('\n')
if not paths:
    print("0 account found")
print(paths)

print('Accounts found:')
for i, path in enumerate(paths):
    if len(path) > 1:
        accountName = path.split("Skype/")[1]
        print(str(i) + " - " + accountName[:-8])
pick = int(input("\nSelect an account : "))

con = lite.connect(paths[pick])
cur = con.cursor()

_NAME = ""
for row in cur.execute('SELECT skypename FROM Accounts'):
    _NAME += row[0]
    break

while True:
    print("\n0 - Exit")
    print("1 - Account infos")
    print("2 - Show contacts")
    print("3 - Show Conversation from contact")
    print("4 - List of calls")
    print("5 - Save all data")
    choice = int(input("\nWhat do you want to do ? "))
    if choice == 0:
        sys.exit()
    if choice == 1:
        account_infos(cur)
    if choice == 2:
        show_contacts(cur)
    if choice == 3:
        conv_from_cont(cur)
    if choice == 4:
        calls_list(cur)
    if choice == 5:
        save_all(cur)
