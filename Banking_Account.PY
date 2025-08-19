class Account:
    
    def __init__(self,balance,account):
        self.balance=balance
        self.account=account
    def debit(self):
        #main_balence=12000
        a=int(input("enter the account number:"))
        d=int(input("enter the ammount that you want to widraw:"))
        if(a==self.account):
            if(self.balance<d):
                print("your ammount is low")
            else:
                self.balance=self.balance-d
        
            print("your curent balance:",self.balance)
        else:
            print("your account number is wrong.")
        return
    def credit(self):
        #main_balence=12000
        a=int(input("enter the account number:"))
        c=int(input("enter the ammount that you want to credit:"))
        if(a==self.account):
            self.balance=self.balance+c
            print("your curent balance:",self.balance)
        else:
            print("your account number is wrong.")
        return
u1=Account(int(input("enter  your balance:")),int(input("enter tour account number:")))
print("credit or debit:")
if(input()=="credit"):
    u1.credit()
else:
    u1.debit()


        
