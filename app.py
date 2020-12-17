from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, FormField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = 'its a secret'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'           #MySQL user name
app.config['MYSQL_PASSWORD'] = 'password'   #password of the database
app.config['MYSQL_DB'] = 'database'         #name of the database

mysql = MySQL(app)

@app.route('/')
def Index():
    cur_1 = mysql.connection.cursor()
    cur_1.execute("SELECT * FROM employee")
    data_1 = cur_1.fetchall()
    cur_1.close()

    cur_2 = mysql.connection.cursor()
    cur_2.execute("SELECT * FROM branch")
    data_2 = cur_2.fetchall()
    cur_2.close()

    cur_3 = mysql.connection.cursor()
    cur_3.execute("SELECT * FROM branch_supplier")
    data_3 = cur_3.fetchall()
    cur_3.close()

    cur_4 = mysql.connection.cursor()
    cur_4.execute("SELECT * FROM client")
    data_4 = cur_4.fetchall()
    cur_4.close()

    cur_5 = mysql.connection.cursor()
    cur_5.execute("SELECT * FROM works_with")
    data_5 = cur_5.fetchall()
    cur_5.close()

    return render_template('display.html', employees=data_1, branches=data_2, branch_suppliers=data_3, clients=data_4, works_with=data_5)


class EmployeeForm(FlaskForm):
    emp_id = StringField(label="Employee ID: ", validators=[DataRequired()])
    first_name = StringField(label="First name: ", validators=[DataRequired()])
    last_name = StringField(label="Last name: ", validators=[DataRequired()])
    birth_day = StringField(label="Date of Birth (YYYY-MM-DD): ", validators=[DataRequired()])
    sex = StringField(label="Sex (M/F): ", validators=[DataRequired()])
    salary = StringField(label="Salary: ", validators=[DataRequired()])
    super_id = StringField(label="Supervisor ID: ", validators=[DataRequired()])
    branch_id = StringField(label="Branch ID: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class DelEmployeeForm(FlaskForm):
    emp_id = StringField(label="Employee ID: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class BranchForm(FlaskForm):
    branch_id = StringField(label="Branch ID: ", validators=[DataRequired()])
    branch_name = StringField(label="Branch name: ", validators=[DataRequired()])
    mgr_id = StringField(label="Manager ID: ", validators=[DataRequired()])
    mgr_start_date = StringField(label="Manager start date (YYYY-MM-DD): ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class DelBranchForm(FlaskForm):
    branch_id = StringField(label="Branch ID: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class ClientForm(FlaskForm):
    client_id = StringField(label="Client ID: ", validators=[DataRequired()])
    client_name = StringField(label="Client name: ", validators=[DataRequired()])
    branch_id = StringField(label="Branch ID: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class DelClientForm(FlaskForm):
    client_id = StringField(label="Client ID: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class WorksWithForm(FlaskForm):
    emp_id = StringField(label="Employee ID: ", validators=[DataRequired()])
    client_id = StringField(label="Client ID: ", validators=[DataRequired()])
    total_sales = StringField(label="Total sales: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class DelWorksWithForm(FlaskForm):
    emp_id = StringField(label="Employee ID: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class BranchSupplierForm(FlaskForm):
    branch_id = StringField(label="Branch ID: ", validators=[DataRequired()])
    supplier_name = StringField(label="Supplier name: ", validators=[DataRequired()])
    supply_type = StringField(label="Supply type: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

class DelSupplierForm(FlaskForm):
    supplier_name = StringField(label="Supplier name: ", validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/update', methods=['GET', 'POST'])
def Update():
    Employee = EmployeeForm()
    Branch = BranchForm()
    Client = ClientForm()
    WorksWith = WorksWithForm()
    Supplier = BranchSupplierForm()

    DelEmployee = DelEmployeeForm()
    DelBranch = DelBranchForm()
    DelClient = DelClientForm()
    DelWorksWith = DelWorksWithForm()
    DelSupplier = DelSupplierForm()

    if Employee.validate_on_submit():
        emp_id = Employee.emp_id.data
        first_name = Employee.first_name.data
        last_name = Employee.last_name.data
        birth_day = Employee.birth_day.data
        sex = Employee.sex.data
        salary = Employee.salary.data
        super_id = Employee.super_id.data
        branch_id = Employee.branch_id.data

        query = "INSERT INTO employee VALUES(%s, '%s', '%s', '%s', '%s', %s, %s, %s);" % (emp_id, first_name, last_name, birth_day, sex, salary, super_id, branch_id)       
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()

        return redirect(url_for('Index'))

    if DelEmployee.validate_on_submit():
        emp_id = DelEmployee.emp_id.data
        query = "DELETE FROM employee WHERE emp_id = %s;" % emp_id
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()
        return redirect(url_for('Index'))

    if Branch.validate_on_submit():
        branch_id = Branch.branch_id.data
        branch_name = Branch.branch_name.data
        mgr_id = Branch.mgr_id.data
        mgr_start_date = Branch.mgr_start_date.data

        query = "INSERT INTO branch VALUES(%s, '%s', %s, '%s');" % (branch_id, branch_name, mgr_id, mgr_start_date)
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()

        return redirect(url_for('Index'))

    if DelBranch.validate_on_submit():
        branch_id = DelBranch.branch_id.data
        query = "DELETE FROM branch WHERE branch_id = %s;" % branch_id
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()
        return redirect(url_for('Index'))

    if Client.validate_on_submit():
        client_id = Client.client_id.data
        client_name = Client.client_name.data
        branch_id = Client.branch_id.data

        query = "INSERT INTO client VALUES(%s, '%s', %s);" % (client_id, client_name, branch_id)
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()

        return redirect(url_for('Index'))

    if DelClient.validate_on_submit():
        client_id = DelClient.client_id.data
        query = "DELETE FROM client WHERE client_id = %s;" % client_id
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()
        return redirect(url_for('Index'))

    if WorksWith.validate_on_submit():
        emp_id = WorksWith.emp_id.data
        client_id = WorksWith.client_id.data
        total_sales = WorksWith.total_sales.data

        query = "INSERT INTO works_with VALUES(%s, %s, %s);" % (emp_id, client_id, total_sales)
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()

        return redirect(url_for('Index'))

    if DelWorksWith.validate_on_submit():
        emp_id = DelWorksWith.emp_id.data
        query = "DELETE FROM works_with WHERE emp_id = %s;" % emp_id
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()
        return redirect(url_for('Index'))

    if Supplier.validate_on_submit():
        branch_id = Supplier.branch_id.data
        supplier_name = Supplier.supplier_name.data
        supply_type = Supplier.supply_type.data

        query = "INSERT INTO branch_supplier VALUES(%s, '%s', '%s');" % (branch_id, supplier_name, supply_type)
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()

        return redirect(url_for('Index'))

    if DelSupplier.validate_on_submit():
        supplier_name = DelSupplier.supplier_name.data
        query = "DELETE FROM branch_supplier WHERE supplier_name = %s;" % supplier_name
        cur = mysql.connection.cursor()
        cur.execute(query)
        mysql.connection.commit()
        return redirect(url_for('Index'))

    return render_template('update.html', Employee=Employee, Branch=Branch, Client=Client, WorksWith=WorksWith, Supplier=Supplier, DelEmployee=DelEmployee, DelBranch=DelBranch, DelClient=DelClient, DelWorksWith=DelWorksWith, DelSupplier=DelSupplier)


if __name__ == "__main__":
    app.run(debug=True)




'''
<form method="post">
            <h2>Delete</h2>
            {{ DelEmployee.emp_id.label }} {{ DelEmployee.emp_id }} <br>
            {{ DelEmployee.submit() }} <br><br>
          </form>
'''
