from flask import Blueprint , render_template, flash,redirect,request,jsonify
from .models import Product , Cart , Wishlist
from flask_login import login_required, current_user
from . import db
from intasend import APIService
from .models import Order

views = Blueprint('views',__name__)

API_PUBLISHABLE_KEY='ISPubKey_test_4f02220a-b88b-48f8-be7e-b5b97957be5c'

API_TOKEN = 'ISSecretKey_test_73e878cb-b90b-4c81-b4df-af746ca8d459'

@views.route('/')
def home():

    items=Product.query.filter_by(flash_sale = True)

    
    return render_template('home.html',items=items, cart = Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else[])

@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)
    item_exists = Cart.query.filter_by(product_link = item_id, customer_link=current_user.id).first()
    if item_exists:
        try:
            item_exists.quantity = item_exists.quantity + 1
            db.session.commit()
            flash(f'Quantity of { item_exists.product.product_name } has been updated')
            return redirect(request.referrer)
        except Exception as e:
            print('Quantity not updated', e)
            flash(f'Quantity of{ item_exists.product_name } not updated')
            return redirect(request.referrer)
        
    new_cart_item = Cart()
    new_cart_item.quantity = 1
    new_cart_item.product_link = item_to_add.id
    new_cart_item.customer_link = current_user.id

    try:
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f'{new_cart_item.product.product_name} added to cart')

    except Exception as e:
        print('Item not added to cart', e)
        flash(f'{new_cart_item.product.product_name} has not been added to cart')
    
    return redirect(request.referrer)

@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.product.current_price * item.quantity

    return render_template('cart.html', cart=cart,amount=amount,total = amount+200)

@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity + 1
        db.session.commit()


        cart = Cart.query.filter_by(customer_link = current_user.id).all()

        amount =0 

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount+200
        }

        return jsonify(data)

@views.route('/minuscart')
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity - 1
        db.session.commit()


        cart = Cart.query.filter_by(customer_link = current_user.id).all()

        amount =0 

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount+200
        }

        return jsonify(data)
    

@views.route('removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link = current_user.id).all()

        amount =0 

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': len(cart),
            'amount': amount,
            'total': amount+200
}

        return jsonify(data)
    

@views.route('/place-order')
@login_required
def place_order():

    customer_cart = Cart.query.filter_by(
        customer_link=current_user.id
    ).all()

    if not customer_cart:
        flash("Cart is empty")
        return redirect('/cart')

    try:

        total = 0

        for item in customer_cart:
            total += item.product.current_price * item.quantity

        # PAYMENT
        service = APIService(
            token=API_TOKEN,
            publishable_key=API_PUBLISHABLE_KEY,
            test=True
        )

        create_order_response = service.collect.mpesa_stk_push(
            phone_number='254712345678',
            email=current_user.email,
            amount=total + 200,
            narrative='Purchase of goods'
        )

        # CREATE ORDER
        for item in customer_cart:

            new_order = Order()

            new_order.quantity = item.quantity
            new_order.price = item.product.current_price
            new_order.status = "Pending"
            new_order.payment_id = create_order_response['id']

            new_order.product_link = item.product_link
            new_order.customer_link = item.customer_link

            db.session.add(new_order)

            # UPDATE STOCK
            product = Product.query.get(item.product_link)

            if product:
                product.in_stock -= item.quantity

            # REMOVE CART
            db.session.delete(item)

        # COMMIT ONLY ONCE
        db.session.commit()

        flash('Order placed Successfully')

        return redirect('/orders')

    except Exception as e:
        print(e)

        flash('Order not placed')

        return redirect('/cart')
        
@views.route('/orders')
@login_required
def order():
    orders = Order.query.filter_by(customer_link = current_user.id).all()
    return render_template('orders.html',orders=orders)


@views.route('/search',methods=['GET','POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search')
        itmes = Product.query.filter(Product.product_name.ilike(f'%{search_query}%')).all()
        return render_template('search.html',items=itmes,cart=Cart.query.filter_by(customer_link=current_user.id).all()
                               if current_user.is_authenticated else[])
    return render_template('search.html')

@views.route('/add-to-wishlist/<int:item_id>')
@login_required
def add_to_wishlist(item_id):

    wishlist_item = Wishlist.query.filter_by(
        product_link=item_id,
        customer_link=current_user.id
    ).first()

    if wishlist_item:
        flash('Already in wishlist')
        return redirect(request.referrer or '/wishlist')

    new_item = Wishlist()
    new_item.product_link = item_id
    new_item.customer_link = current_user.id

    db.session.add(new_item)
    db.session.commit()

    flash('Added to wishlist')

    return redirect( '/wishlist')

@views.route('/wishlist')
@login_required
def wishlist():

    wishlist_items = Wishlist.query.filter_by(
        customer_link=current_user.id
    ).all()

    cart = Cart.query.filter_by(
        customer_link=current_user.id
    ).all()

    return render_template(
        'wishlist.html',
        wishlist_items=wishlist_items,
        cart=cart
    )