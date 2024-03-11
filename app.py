# app.py

import io
from flask import Flask, Response, render_template, request, redirect, url_for
import pandas as pd
import plotly.express as px
from io import StringIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate




csv_filepath = "/Users/chris/Desktop/Codes/ReportDashboardPython/csv_dashboard/output_cleanfile.csv"

app = Flask(__name__)

#auth

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(20), nullable=False, unique=True)
        password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')



df = pd.read_csv(csv_filepath)


#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


#logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)



# Function to get the top 10 performers based on a given metric and return the Plotly figure
def get_top_performers_chart(metric_column):
    top_performers = df.nlargest(10, metric_column)[['Company Name', metric_column]]
    fig = px.bar(top_performers, x="Company Name", y=metric_column,
                 title=f"Top 10 Performers - {metric_column}",
                 labels={metric_column: 'Metric Value'}, color="Company Name")
    return fig

#landing page
# @app.route("/")
# def landing_page():
#     return render_template("index.html")

#home page
# @app.route('/home', methods=['GET', 'POST'])
# def home():
#     total_customers = df['Company Name'].nunique()
#     total_doc_titles = df['Doc Type Title'].nunique()

#     selected_customer = request.form.getlist('customer_name')
#     selected_month = request.form.getlist('selected_month') or ['2023-11']  # Default to 2023-11 if not provided

#     if selected_customer:
#         # Filter DataFrame based on selected customers and months
#         filtered_df = df[(df['Company Name'].isin(selected_customer)) & (df[selected_month].notnull().any(axis=1))]

#         # Create a bar chart using Plotly
#         fig = px.bar(filtered_df, x='Doc Type Title', y=selected_month, title=f'Doc Type Titles for {", ".join(selected_customer)} - {", ".join(selected_month)}')

#         # Convert the Plotly figure to JSON to pass to the template
#         chart_json = fig.to_json()

#         return render_template('home.html', total_customers=total_customers, total_doc_titles=total_doc_titles, chart_json=chart_json, selected_customer=selected_customer, selected_month=selected_month, df=df)

#     return render_template('home.html', total_customers=total_customers, total_doc_titles=total_doc_titles, selected_customer=None, chart_json=None, selected_month=['2023-11'], df=df)



@app.route('/home', methods=['GET', 'POST'])
def home():
    total_customers = df['Company Name'].nunique()
    total_doc_titles = df['Doc Type Title'].nunique()

    selected_customer = request.form.get('customer_name')
    selected_month = request.form.get('selected_month', '2023-11')  # Default to 2023-11 if not provided

    if selected_customer:
        # Filter DataFrame based on selected customer and month
        filtered_df = df[(df['Company Name'] == selected_customer) & (df[selected_month].notnull())]

        # Create a bar chart using Plotly
        fig = px.bar(filtered_df, x='Doc Type Title', y=selected_month, title=f'Doc Type Titles for {selected_customer} - {selected_month}')

        # Convert the Plotly figure to JSON to pass to the template
        chart_json = fig.to_json()

        return render_template('home.html', total_customers=total_customers, total_doc_titles=total_doc_titles, chart_json=chart_json, selected_customer=selected_customer, selected_month=selected_month, df=df)

    return render_template('home.html', total_customers=total_customers, total_doc_titles=total_doc_titles, selected_customer=None, chart_json=None, selected_month='2023-11', df=df)
#download code
@app.route('/download/<string:customer>/<string:month>')
def download_csv(customer, month):

    #test 
 
    # Filter DataFrame based on selected customer and month
    filtered_df = df[(df['Company Name'] == customer) & (df[month].notnull())]

    # Create a CSV file in-memory
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)

    # Return the CSV file as a downloadable response
    response = Response(csv_buffer.getvalue(), content_type='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={customer}_{month}_filtered_data.csv'

    return response



# Main dashboard with initial visualization
@app.route("/dashboard")
def dashboard():
    # Filter data based on selected month
    selected_month = request.args.get('month', '2023-11')  # Default to November 2023
    filtered_df = df[['Company Name', selected_month]]

    # Sort DataFrame by selected month in descending order
    filtered_df = filtered_df.sort_values(by=selected_month, ascending=False)

    # Prepare data for the chart
    fig = px.bar(filtered_df, x="Company Name", y=selected_month,
                 title=f"Credits Used by Company - {selected_month}",
                 labels={selected_month: 'Credits Used'}, color="2023-11")

    # Pass data, figure, top performers, and selected month to the template
    return render_template("dashboard.html", data=df.to_json(), fig=fig.to_json(),
                           top_performers=get_top_performers_chart(selected_month).to_json(), selected_month=selected_month, df=df)

#try
# Pass data, figure, top performers, and selected month to the template
    # return render_template("dashboard.html", data=df.to_json(), fig=fig.to_json(),
    #                    top_performers=get_top_performers_chart(selected_month), selected_month=selected_month)

@app.route("/details/<company_name>")
def details(company_name):
    # Filter data for the selected company name
    company_data = df[df['Company Name'] == company_name]

    # Prepare data for the detailed chart
    fig_details = px.bar(company_data, x="Doc Type Title", y="2023-11",
                         title=f"Credits Used Breakup for {company_name}",
                         labels={'Credits Used': 'Credits Used'}, color="Doc Type Title")

    # Pass the data and figure to the template
    return render_template("details.html", company_name=company_name, data=company_data.to_json(), fig_details=fig_details.to_json())

# Top 10 companies dashboard
@app.route("/top10")
def top10_dashboard():
    # You can choose a different metric for the top 10 companies, e.g., '2023-11'
    metric_column = '2023-11'
    fig = get_top_performers_chart(metric_column)

    # Pass data and figure to the template
    return render_template("top10_dashboard.html", data=df.to_json(), fig=fig.to_json(), metric_column=metric_column)

# Route to view credit usage month-wise
# @app.route("/c")

# def credit_usage():
#     # Calculate total credit usage for each customer
#     df['Total Credit Usage'] = df[['2023-11', '2023-12', '2024-01', '2024-02']].sum(axis=1)

#     # Create a Plotly bar chart
#     fig = px.bar(df, x='Company Name', y='Total Credit Usage',
#                  labels={'Total Credit Usage': 'Total Credit Usage'},
#                  title='Total Credit Usage Across Four Months')

#     # Customize the layout if needed
#     fig.update_layout(height=600, width=800)

#     # Pass the Plotly figure to the template
#     return render_template("credit_usage.html", fig=fig.to_json())

# Route to view month-wise credit usage

@app.route("/credit_usage")
def credit_usage():
    # Calculate total credits used for each month
    credit_usage = df[['2023-11', '2023-12', '2024-01', '2024-02']].sum()

    # Create a Plotly bar chart
    fig = px.bar(x=credit_usage.index, y=credit_usage.values,
                 labels={'x': 'Month', 'y': 'Total Credits Used'},
                 title='Total Credits Used for Each Month')

    # Customize the layout if needed
    fig.update_layout(height=600, width=800)

    # Pass the Plotly figure to the template
    return render_template("credit_usage.html", fig=fig.to_json())


if __name__ == "__main__":
    app.run(debug=True)
