# Code Mart

A Django-based platform ("CodeMart") where developers can upload, showcase, and sell digital content (code snippets, designs, articles) and customers can browse, preview, purchase, and communicate with developers.

---

## Features

**Role-Based Access**: _Separate Developer and Customer signups with custom dashboards._

**Content Upload**: _Developers add content with metadata (title, description, price, tags, category)._

**Live Preview**: _In-browser preview of HTML/CSS/JS content without exposing source code._

**Shopping Cart**: _Add multiple items (content & subscriptions) and manage in-cart items._

**Secure Checkout**: _Integration with Razorpay and PayPal for seamless payments._

**Subscription Plans**: _Customers subscribe to unlock chat access; developers chat for free._

**Messaging**: _Secure one-on-one chat for custom requests, negotiations, and support._

**Admin Panel**: _Manage users, content, subscriptions, and handle disputes._

## Tech Stack

**Backend**: _Python, Django_

**Frontend**: _HTML5, Bootstrap, CSS3, JavaScript_

**Database**: _MySQL_

**Payments**: _Razorpay, PayPal_

## Installation & Setup

### Clone the repo:

_git clone https://github.com/Chaurasiavipul98/Code-Mart.git
cd code-mart_

### Create & activate virtualenv:

_python3 -m venv venv
source venv/bin/activate_

### Install dependencies:

_pip install -r requirements.txt_

### Configure environment variables:

#### Create a .env file in the project root with:

_SECRET_KEY=your_django_secret_key_

_DEBUG=True_

_DB_NAME=your_mysql_db_

_DB_USER=mysql_user_

_DB_PASSWORD=mysql_password_

_RAZORPAY_KEY=your_key_

_RAZORPAY_SECRET=your_secret_

### Run migrations & collect static files:

_python manage.py migrate
python manage.py collectstatic_

### Run the development server:

_python manage.py runserver_

_Visit http://127.0.0.1:8000/ in your browser._

## Usage

**Sign up as a Developer or Customer.**

**Developers upload content under the "Marketplace" tab.**

**Customers browse and preview content, add items or subscriptions to the cart.**

**Complete payment via Razorpay or PayPal.**

**Subscribed customers can chat with developers via the "Messages" page.**

**Admin can manage users, content, and disputes via Django admin.**

## Contributing

**Fork the repository.**

**Create a feature branch (git checkout -b feature/new-feature).**

**Commit your changes (git commit -m "Add new feature").**

**Push to branch (git push origin feature/new-feature).**

### Could you submit a Pull Request?

## License

### _This project is licensed under the MIT License. See the LICENSE file for details._

## Contact - For questions or feedback, reach out to:

### Vipul Chaurasia (Developer)

#### Email: _chaurasiavipul98@gmail.com_

#### LinkedIn: _linkedin.com/in/vipulchaurasia_
