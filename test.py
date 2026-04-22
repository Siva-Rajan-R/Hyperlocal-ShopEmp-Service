a={'name':'name','type':'TEXT','required':True}

b={'name':'name','type':'TEXT','requires':True,'dd_values':None}

c={**a,**b}

print(c)

if len(b)==len(c):
    print("present")
else:
    print("not present")


from pydantic import BaseModel,EmailStr
a=1

print(type(a)==int)