import pickle
import os 
file = open("data_spin/DATA-FULL.txt","r",encoding="utf-8")
document_data = {}
print(file)
for i in file.readlines():
  i = i.replace("{","")
  i = i.replace("}","")
  i = i.replace("\n","")
  h = i.split("|")
  print(h)
  for jj in h:
    pu = h
    print(h)
    pu.remove(jj)
    print(pu)
    document_data[jj] = pu
with open("dataspin.p","wb") as file:
    pickle.dump(document_data,file)
