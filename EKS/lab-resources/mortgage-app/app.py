from operator import contains
import os
from urllib import response
from datetime import date
from flask import Flask, session, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import dynamodb_handler as dynamodb

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)
  
# MAIN
@app.route('/')
@app.route("/mortgage")
def dashboard():
    return render_template("home.html", home=True)

@app.route("/mortgage/viewaccount" , methods=["GET", "POST"])
def viewaccount():
    if request.method == "POST":
        acc_id = request.form.get("acc_id")
        cust_id = request.form.get("cust_id")
        items = {}
        if (acc_id != ""):
            response = dynamodb.getAccountDetailsByAcctId(int(acc_id))
            items=response['Items']
        
        print('data', items)
        if items:
            return render_template('viewaccount.html', viewaccount=True, data=items)
    
        flash("Account not found! Please,Check you input.", 'danger')
    return render_template('viewaccount.html', viewaccount=True)


@app.route("/mortgage/viewaccountstatus" , methods=["GET", "POST"])
def viewaccountstatus():
    return render_template('viewaccountstatus.html', viewaccountstatus=True)

# Code for pay amount 
@app.route('/mortgage/pay',methods=['GET','POST'])
@app.route('/mortgage/pay/<acc_id>',methods=['GET','POST'])
def pay(acc_id=None):
    
    if acc_id is None:
        return redirect(url_for('viewaccount'))
    else:
        if request.method == "POST":
            print('in post pay', acc_id)
            amount = request.form.get("amount")
            print('amount', amount)
            response=dynamodb.getAccountDetailsByAcctId(int(acc_id))
            if response['Items'] is not None:
                updatedBalance = int(response['Items'][0]['balance'] - int(amount))
                result=dynamodb.updateAcctBalance(int(acc_id), updatedBalance)
                flash(f"Transaction completed. The amount of ${amount} has been credited from account {acc_id}.",'success')
                dynamodb.insertTransactions(acc_id,"Amount paid",amount)
            else:
                flash(f"Account not found or Deactivated.",'danger')
        else:
            response = dynamodb.getAccountDetailsByAcctId(int(acc_id))
            if response['Items'] is not None:
                return render_template('pay.html', pay=True, data=response['Items'])
            else:
                flash(f"Account not found or Deactivated.",'danger')

    return redirect(url_for('viewaccount'))

# code for view account statement based on the account id
# Using number of last transaction
@app.route("/mortgage/statement" , methods=["GET", "POST"])
def statement():   
    if request.method == "POST":
        acc_id = request.form.get("acc_id")
        number = request.form.get("number")
        flag = request.form.get("Radio")
        if flag=="red":
            data = dynamodb.getTransactions(int(acc_id), number)
        if data:
            print(data)
            return render_template('statement.html', statement=True, data=data['Items'], acc_id=acc_id)
        else:
            flash("No Transactions", 'danger')
            return redirect(url_for('dashboard'))
    return render_template('statement.html', statement=True)

# route for 404 error
@app.errorhandler(404)
def not_found(e):
  return render_template("404.html") 
   
# Main
if __name__ == '__main__':
   # app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=80)
