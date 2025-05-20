# Digital Content Marketplace

A Django-based platform ("CodeMart") where developers can upload, showcase, and sell digital content (code snippets, designs, articles) and customers can browse, preview, purchase, and communicate with developers.

---

## Features

* **Role-Based Access**: Separate **Developer** and **Customer** signup with custom dashboards.
* **Content Upload**: Developers add content with metadata (title, description, price, tags, category).
* **Live Preview**: In-browser preview of HTML/CSS/JS content without exposing source code.
* **Shopping Cart**: Add multiple items (content & subscriptions) and manage in-cart items.
* **Secure Checkout**: Integration with **Razorpay** for seamless payments.
* **Subscription Plans**: Customers subscribe to unlock chat access; developers chat for free.
* **Messaging**: Secure one-on-one chat for custom requests, negotiations, and support.
* **Admin Panel**: Manage users, content, subscriptions, and handle disputes.

---

## Tech Stack

* **Backend**: Python, Django
* **Frontend**: HTML5, Bootstrap, CSS3, JavaScript
* **Database**: MySQL
* **Payments**: Razorpay

---

## Installation & Setup

1. **Clone the repo**:

   ```bash
   git clone https://github.com/chaurasiavipul98/code-mart.git
   cd code-mart
   ```

2. **Create & activate virtualenv**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:

   * Create a `.env` file in the project root with:

     ```env
     SECRET_KEY=your_django_secret_key
     DEBUG=True
     DB_NAME=your_mysql_db
     DB_USER=mysql_user
     DB_PASSWORD=mysql_password
     RAZORPAY_KEY=your_key
     RAZORPAY_SECRET=your_secret
     ```

5. **Run migrations & collect static files**:

   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

6. **Run the development server**:

   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000/` in your browser.

---

## Usage

* **Sign up** as Developer or Customer.
* Developers upload content under the "Marketplace" tab.
* Customers browse and preview content; add items or subscriptions to the cart.
* Complete payment via Razorpay or PayPal.
* Subscribed customers can chat with developers via the "Messages" page.
* Admin can manage users, content, and disputes via Django admin.

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -m "Add new feature"`).
4. Push to branch (`git push origin feature/new-feature`).
5. Submit a Pull Request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or feedback, reach out to:

* **Vipul Chaurasia** (Developer)
* Email: [chaurasiavipul98@gmail.com](mailto:chaurasiavipul98@gmail.com)
* LinkedIn: [linkedin.com/in/vipulchaurasia](https://linkedin.com/in/vipulchaurasia)
