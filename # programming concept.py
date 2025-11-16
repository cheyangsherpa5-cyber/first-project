# programming concept
''''
phone_number='image.jpg'
result=phone_number.rfind('m')-len(phone_number)
print(result)

domain_name='ram123@gmail.com'
print(domain_name[domain_name.rfind('@'):])
print(result)

name=input("Enter your full name:")
name="_".join(name.strip().split().lowercase())
print(name)'''
'''

password=input("Enter your secret password:")
code=(password.lower()
.replace("a","@")
.replace("s","$")
.replace("o","0")
.replace("i","1")
.replace("e","3"))
code=code+"0##9"
print("your secret password:",code)
'''
#or you can follow this method
password=input("Enter your secretpassword:").lower()
result=password.maketrans('aeios','@310$')
print(f"your secret code:{password.translate(result)}0##9")


      
    