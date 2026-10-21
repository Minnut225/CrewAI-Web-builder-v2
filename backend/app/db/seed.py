import logging
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.menu_order import (
    Category,
    Product,
    Ingredient,
    Recipe,
    Order,
    OrderItem,
    Payment,
    PaymentMethod,
    PaymentStatus,
    OrderStatus,
    OrderType,
    StockMovement,
    MovementType,
)

logger = logging.getLogger(__name__)


def seed_database(db: Session) -> None:
    """
    Seeds initial default users, categories, ingredients, products with recipes,
    and demo transaction records for CoffeeFlow POS.
    Idempotent: skips existing records if already seeded.
    """
    logger.info("Starting database seeding process...")

    # 1. Seed Users
    manager = db.query(User).filter(User.username == "manager").first()
    if not manager:
        manager = User(
            username="manager",
            hashed_password=get_password_hash("password123"),
            full_name="Nguyễn Mai Lan",
            role=UserRole.MANAGER,
            is_active=True,
        )
        db.add(manager)
        db.flush()

    cashier = db.query(User).filter(User.username == "cashier").first()
    if not cashier:
        cashier = User(
            username="cashier",
            hashed_password=get_password_hash("password123"),
            full_name="Trần Thu Ngân",
            role=UserRole.CASHIER,
            is_active=True,
        )
        db.add(cashier)
        db.flush()

    manager1 = db.query(User).filter(User.username == "manager1").first()
    if not manager1:
        manager1 = User(
            username="manager1",
            hashed_password=get_password_hash("password123"),
            full_name="Manager One",
            role=UserRole.MANAGER,
            is_active=True,
        )
        db.add(manager1)
        db.flush()

    cashier1 = db.query(User).filter(User.username == "cashier1").first()
    if not cashier1:
        cashier1 = User(
            username="cashier1",
            hashed_password=get_password_hash("password123"),
            full_name="Cashier One",
            role=UserRole.CASHIER,
            is_active=True,
        )
        db.add(cashier1)
        db.flush()

    # 2. Seed Categories
    categories_data = [
        {"name": "Cà phê truyền thống", "display_order": 1},
        {"name": "Cà phê máy", "display_order": 2},
        {"name": "Trà & Macchiato", "display_order": 3},
        {"name": "Bánh ngọt", "display_order": 4},
    ]

    cat_map = {}
    for c_info in categories_data:
        cat = db.query(Category).filter(Category.name == c_info["name"]).first()
        if not cat:
            cat = Category(
                name=c_info["name"],
                display_order=c_info["display_order"],
                is_active=True,
            )
            db.add(cat)
            db.flush()
        cat_map[c_info["name"]] = cat

    # 3. Seed Ingredients
    ingredients_data = [
        {
            "name": "Cà phê Robusta Đắk Lắk",
            "sku": "ING-ROB-01",
            "unit": "g",
            "stock_quantity": 25000.0,
            "min_stock_level": 2000.0,
            "cost_per_unit": 180,
        },
        {
            "name": "Cà phê Arabica Cầu Đất",
            "sku": "ING-ARA-02",
            "unit": "g",
            "stock_quantity": 20000.0,
            "min_stock_level": 2000.0,
            "cost_per_unit": 250,
        },
        {
            "name": "Sữa đặc Phương Nam",
            "sku": "ING-SUA-03",
            "unit": "g",
            "stock_quantity": 15000.0,
            "min_stock_level": 1500.0,
            "cost_per_unit": 80,
        },
        {
            "name": "Sữa tươi Dalat Milk thanh trùng",
            "sku": "ING-MILK-04",
            "unit": "ml",
            "stock_quantity": 30000.0,
            "min_stock_level": 3000.0,
            "cost_per_unit": 45,
        },
        {
            "name": "Kem béo mặn Cố Đô",
            "sku": "ING-KEM-05",
            "unit": "g",
            "stock_quantity": 8000.0,
            "min_stock_level": 800.0,
            "cost_per_unit": 120,
        },
        {
            "name": "Trà lài thượng hạng",
            "sku": "ING-TRA-06",
            "unit": "g",
            "stock_quantity": 10000.0,
            "min_stock_level": 1000.0,
            "cost_per_unit": 150,
        },
        {
            "name": "Đào ngâm Hy Lạp",
            "sku": "ING-DAO-07",
            "unit": "g",
            "stock_quantity": 10000.0,
            "min_stock_level": 1000.0,
            "cost_per_unit": 110,
        },
        {
            "name": "Cam vàng Mỹ",
            "sku": "ING-CAM-08",
            "unit": "pcs",
            "stock_quantity": 200.0,
            "min_stock_level": 20.0,
            "cost_per_unit": 8000,
        },
        {
            "name": "Hạt sen Huế ninh nhừ",
            "sku": "ING-SEN-09",
            "unit": "g",
            "stock_quantity": 8000.0,
            "min_stock_level": 800.0,
            "cost_per_unit": 160,
        },
        {
            "name": "Bơ lạt & Bột mì Pháp",
            "sku": "ING-BANH-10",
            "unit": "g",
            "stock_quantity": 15000.0,
            "min_stock_level": 1500.0,
            "cost_per_unit": 95,
        },
    ]

    ing_map = {}
    for ing_info in ingredients_data:
        ing = db.query(Ingredient).filter(Ingredient.sku == ing_info["sku"]).first()
        if not ing:
            ing = Ingredient(
                name=ing_info["name"],
                sku=ing_info["sku"],
                unit=ing_info["unit"],
                stock_quantity=ing_info["stock_quantity"],
                min_stock_level=ing_info["min_stock_level"],
                cost_per_unit=ing_info["cost_per_unit"],
            )
            db.add(ing)
            db.flush()

            # Record initial import movement
            movement = StockMovement(
                ingredient_id=ing.id,
                user_id=manager.id,
                change_amount=ing_info["stock_quantity"],
                movement_type=MovementType.IMPORT,
                reference_id="INIT-SEED",
                note="Khởi tạo tồn kho ban đầu",
            )
            db.add(movement)
        ing_map[ing_info["sku"]] = ing

    # 4. Seed Products with Recipes
    products_data = [
        {
            "sku": "CF-MUE-01",
            "name": "Cà phê Muối Cố Đô",
            "category_name": "Cà phê truyền thống",
            "price": 45000,
            "cost_price": 14500,
            "description": "Robusta Đắk Lắk + Kem béo mặn Cố Đô công thức độc quyền",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuBFJ7WeGOZuuiIWKkUMUsz2ulGOXZP9RK6A88EVJl-yzAQOeqKLRtGm8L-boUZLne8wOqg9jmwo6nawPM7EMwrVrekNKBxJqxqnd19B6qAo1WNCglml-GKT0FRk_g6aaFsJHsmNDQbzZ9hpRckzDBMTi2rCPPLvQo_a9qxXKP71cG1rqBIg0u5ZZSoNVGxJQHOvdsodBANEMKrg8ZTjdz36gKlnX_Z8gddsLtfUQY-XVUEDT-X5gHPO0A",
            "recipes": [
                {"ing_sku": "ING-ROB-01", "qty": 25.0},
                {"ing_sku": "ING-SUA-03", "qty": 30.0},
                {"ing_sku": "ING-KEM-05", "qty": 40.0},
            ],
        },
        {
            "sku": "CF-BAC-02",
            "name": "Bạc sỉu 3 tầng",
            "category_name": "Cà phê truyền thống",
            "price": 40000,
            "cost_price": 11500,
            "description": "Sữa đặc Phương Nam, sữa tươi Dalat Milk thanh trùng, cà phê phin",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuBQfRrLFHQA1nmauniMrwzsglXwArsD4RiNwyBgP4viUoMmgsm5lIvpAnD5x9RaaaZxRDYCkmkPQW6QIc4wN5TTLNkwAXrumwniBeX4QG8vJdIpx2mObXUuQZWI_xmW_V-pVHfsH8HMkBhcGksFVkw605A0_7LuZd06W7VwQQSMMw_VwN76aKedZdyCX6r7knOh447lDOtbZkgtiRvq46z8XqtHhGwbIu5JgCuQbaUVQ3ELfpyd_-ZEGQ",
            "recipes": [
                {"ing_sku": "ING-ROB-01", "qty": 20.0},
                {"ing_sku": "ING-SUA-03", "qty": 40.0},
                {"ing_sku": "ING-MILK-04", "qty": 60.0},
            ],
        },
        {
            "sku": "CF-DEN-03",
            "name": "Cà phê Đen đá",
            "category_name": "Cà phê truyền thống",
            "price": 29000,
            "cost_price": 5000,
            "description": "Hạt Robusta mộc rang vừa, chiết xuất phin chuẩn vị truyền thống",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuC8g6zpSJ02FnVCt97G9-5De7xqJjG57QuVmDQbDBoL-RQ7bKYcWBaBTbQRYanl4CSDHP-0tFhz1yn5qk6S_nfdiqQE5bBO8OCaTYxjGTlirKk8IGLAeFxyzvj1nPCmcepAfYApKVcEWx1BhVrfkpOcxkFj27Lj5qzdCFjqCicYwAGOjUW-IInhqi8aZuE9HYUR9opRk0_yhwxL58N3LP0Ngn7csoMTPa5fDNXuodITsEMpZh1COUk1mQ",
            "recipes": [
                {"ing_sku": "ING-ROB-01", "qty": 25.0},
            ],
        },
        {
            "sku": "CF-NAU-04",
            "name": "Cà phê Nâu đá",
            "category_name": "Cà phê truyền thống",
            "price": 32000,
            "cost_price": 7500,
            "description": "Cà phê phin đậm đà hòa quyện cùng sữa đặc Phương Nam béo ngậy",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuByGeVsQdxyheo5AWF3Z12GlXuq0uQ3oR3Cxwo99qkAE4_3Q62FsMfbixFFeQee-80MfdR4KyzfnLTqsPY4YSEmIajlIubB_O6jRxDQknHbF1mm_89JZWyrGedVfLxA9JqjaU9VrbiaHSQaT-cseO6AdrufeU80yfvbmjyeiPr_8_LTE2zdKUbwYJxqfW_60poSZ8fNINEc9J9-yMF0NOssAQDhHLVSgkj1jmakUpLGhKNmQ-lcZiAWzg",
            "recipes": [
                {"ing_sku": "ING-ROB-01", "qty": 25.0},
                {"ing_sku": "ING-SUA-03", "qty": 35.0},
            ],
        },
        {
            "sku": "CF-CB-05",
            "name": "Cold Brew Cam Vàng",
            "category_name": "Cà phê máy",
            "price": 50000,
            "cost_price": 16500,
            "description": "Arabica Cầu Đất ủ lạnh 16 tiếng kết hợp cam vàng Mỹ mọng nước",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDjZBljh8XegXeSCoYlt2mMwSdEkZV3rbwQfgShM4jaXeOmu18rKcQRqZw5kwYOVO76fkOv3gwHdrCquoukDJKab0mW68LMn4F8wQwsxp1CeOPMnrDzof13GUVKcypDIdlKixvq6SuUDpkLnNEDWkKeFTR0zQWGcWFVVD4D-Scyg9sbWg6qz0arTad3Hpsdac9AmrSP7omk2MkS5dmHiCZ4xZRDCzCCQO2jixxsaK_hKgSIVU_iAKeqcA",
            "recipes": [
                {"ing_sku": "ING-ARA-02", "qty": 30.0},
                {"ing_sku": "ING-CAM-08", "qty": 1.0},
            ],
        },
        {
            "sku": "TEA-DAO-06",
            "name": "Trà Đào Cam Sả",
            "category_name": "Trà & Macchiato",
            "price": 48000,
            "cost_price": 13500,
            "description": "Trà lài thượng hạng ủ lạnh, đào miếng giòn ngọt, cam vàng thơm mát",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDzmHHCKwHiSV-A_6-604ENcutCdaR1q3BpTDI0SB0SQp9kyoG4HglVmeB49GPZ3Fv4_DUgMFUDWvisjeu3bF86cCN3gQXMaOiXHlDiWuTJ9UbNQKPyU25-EqL-l7LMh7V0yguP4BRL1E4mvesGYxptMcJpG0IeP2rhR_ejo7HU9qx69fK4ebh2tX1su-1p08ZVZCrjybLUs2VLv1hzlJttOYRNwD9FAPOs3RlDgPfzbiUMIl5n85golw",
            "recipes": [
                {"ing_sku": "ING-TRA-06", "qty": 15.0},
                {"ing_sku": "ING-DAO-07", "qty": 50.0},
                {"ing_sku": "ING-CAM-08", "qty": 0.5},
            ],
        },
        {
            "sku": "TEA-MC-07",
            "name": "Trà Mãng Cầu Đắk Lắk",
            "category_name": "Trà & Macchiato",
            "price": 45000,
            "cost_price": 12500,
            "description": "Mãng cầu tươi Đắk Lắk rim đường phèn trên nền cốt trà lài thơm nồng",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuCQeNcCpQnwKN5ZWxzU4vKu2vj5oRPnfwsp1LcrZFtxk3N9OKU9D72sh56nCeXf5yMjmElOAsdZwLwI80jrDHV_kNeo9FRhJsMHxsoZs3-f85cSPY39Epw2y24dsWBypiwKNfd1tSpVibHtK-NIe3z-g6gg3EW7wXoITOWP4f1TmbNryZMHQhtu_p_NIPJMPtenChijF54rQulvzY0RB07-pU7xzJRCmGxM29mcSF1ZkzZ9zyCEBu2MLA",
            "recipes": [
                {"ing_sku": "ING-TRA-06", "qty": 15.0},
            ],
        },
        {
            "sku": "TEA-SEN-08",
            "name": "Trà Ô Long Sen Vàng",
            "category_name": "Trà & Macchiato",
            "price": 52000,
            "cost_price": 16000,
            "description": "Hạt sen Huế ninh nhừ bùi ngậy, củ năng giòn và cốt trà đậm đà",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDbyE5dARftZ03nv0FCh6hvPbhtE0R1P0W-oOsH4jOeL2ZjM1i3PJPtL6C3KLxUsjcDrF1Lx2McsRx7R_r6e4Zj68VYA7WFhm6Pbcf_dSfPA0pqfAqugDukZPRfiVZuBJirOpSUiCm_DVfiqN4ZQUC1oVp-Ki3sYrve_3ElruUqU8oldtkcgYi-XF-cG7MeGVvlQFJ5D6VGXYIl4tWXZ5GT5GxlWNfqwFMFX4olGNDBB7WzVY-d0VbR1Q",
            "recipes": [
                {"ing_sku": "ING-TRA-06", "qty": 15.0},
                {"ing_sku": "ING-SEN-09", "qty": 50.0},
            ],
        },
        {
            "sku": "PAST-CR-09",
            "name": "Croissant Bơ Tỏi",
            "category_name": "Bánh ngọt",
            "price": 35000,
            "cost_price": 10500,
            "description": "Bánh sừng bò nướng giòn thơm bơ Pháp kết hợp xốt bơ tỏi lá mùi tây",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDF2sRjD-qQ239p8_iP9Dskq_1vQ08vL3GgV8tS0HwU8sWlQ6X9_Zk8yM8V3jKq0",
            "recipes": [
                {"ing_sku": "ING-BANH-10", "qty": 100.0},
            ],
        },
        {
            "sku": "PAST-TIR-10",
            "name": "Tiramisu Cacao",
            "category_name": "Bánh ngọt",
            "price": 42000,
            "cost_price": 13000,
            "description": "Bánh Tiramisu Ý truyền thống thấm đẫm cà phê Arabica và bột cacao",
            "image_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuA4brGiopypLHG6XkxTBoc-kS4U_AwQLkjvp3ZJwB3kzI9qlRQUpA4jm9QYdTKahXu9ILO7UKt5vh0kvNPiE9b1XT95ZwIiT9Gq8jjFr0MvuU-rjIY4daaD_1EGFCG8zZjhSiLP_wHD8tTXqnWXOO-Pso1vgkF_p4C5fHgDIeOid3u_zjGnDxFf4YlkxvdGKFZW2oLzKgrzoKwmiXoOwWD-N1w-W644_s-z9XxyNxlTZRq9uaRAwvM0Bg",
            "recipes": [
                {"ing_sku": "ING-BANH-10", "qty": 80.0},
                {"ing_sku": "ING-ARA-02", "qty": 10.0},
            ],
        },
    ]

    prod_map = {}
    for p_info in products_data:
        prod = db.query(Product).filter(Product.sku == p_info["sku"]).first()
        cat = cat_map.get(p_info["category_name"])
        if not prod and cat:
            prod = Product(
                category_id=cat.id,
                name=p_info["name"],
                sku=p_info["sku"],
                price=p_info["price"],
                cost_price=p_info["cost_price"],
                image_url=p_info["image_url"],
                description=p_info["description"],
                is_available=True,
            )
            db.add(prod)
            db.flush()

            for r_item in p_info["recipes"]:
                ing = ing_map.get(r_item["ing_sku"])
                if ing:
                    recipe = Recipe(
                        product_id=prod.id,
                        ingredient_id=ing.id,
                        quantity_required=r_item["qty"],
                    )
                    db.add(recipe)
        prod_map[p_info["sku"]] = prod

    # 5. Seed Demo Orders for Manager Dashboard
    existing_orders_count = db.query(Order).count()
    if existing_orders_count == 0:
        logger.info("Seeding realistic demo POS orders for dashboard metrics...")
        demo_orders_spec = [
            {
                "code": "ORD-1042",
                "channel": "Bàn 04 (Tầng 1)",
                "type": OrderType.DINE_IN,
                "status": OrderStatus.COMPLETED,
                "items": [
                    {"sku": "CF-MUE-01", "qty": 2, "note": "Size L, 50% đường, 70% đá"},
                    {"sku": "PAST-CR-09", "qty": 1, "note": "Hâm nóng"},
                ],
                "discount": 10000,
                "minutes_ago": 15,
            },
            {
                "code": "ORD-1041",
                "channel": "Mang đi #12",
                "type": OrderType.TAKEAWAY,
                "status": OrderStatus.COMPLETED,
                "items": [
                    {"sku": "CF-CB-05", "qty": 1, "note": "Ít đá"},
                    {"sku": "PAST-CR-09", "qty": 1, "note": ""},
                ],
                "discount": 0,
                "minutes_ago": 30,
            },
            {
                "code": "ORD-1040",
                "channel": "Bàn 02 (Quầy bar)",
                "type": OrderType.DINE_IN,
                "status": OrderStatus.COMPLETED,
                "items": [
                    {"sku": "TEA-DAO-06", "qty": 2, "note": "100% đường, 100% đá, thêm thạch đào"},
                    {"sku": "CF-DEN-03", "qty": 1, "note": "Không đường"},
                ],
                "discount": 5000,
                "minutes_ago": 50,
            },
            {
                "code": "ORD-1039",
                "channel": "Bàn 09 (Sân vườn)",
                "type": OrderType.DINE_IN,
                "status": OrderStatus.COMPLETED,
                "items": [
                    {"sku": "CF-BAC-02", "qty": 3, "note": "Ít ngọt"},
                    {"sku": "PAST-TIR-10", "qty": 1, "note": ""},
                ],
                "discount": 12000,
                "minutes_ago": 75,
            },
            {
                "code": "ORD-1038",
                "channel": "Mang đi #11",
                "type": OrderType.TAKEAWAY,
                "status": OrderStatus.COMPLETED,
                "items": [
                    {"sku": "TEA-SEN-08", "qty": 1, "note": "50% đá, ít ngọt"},
                ],
                "discount": 0,
                "minutes_ago": 110,
            },
        ]

        now = datetime.now(UTC)
        for ord_info in demo_orders_spec:
            created_time = now - timedelta(minutes=ord_info["minutes_ago"])
            subtotal = 0
            order_items_to_add = []

            for item_spec in ord_info["items"]:
                product = prod_map.get(item_spec["sku"])
                if product:
                    item_subtotal = product.price * item_spec["qty"]
                    subtotal += item_subtotal
                    order_items_to_add.append(
                        OrderItem(
                            product_id=product.id,
                            quantity=item_spec["qty"],
                            unit_price=product.price,
                            subtotal=item_subtotal,
                            note=item_spec["note"],
                        )
                    )

            total_amount = max(0, subtotal - ord_info["discount"])

            order = Order(
                order_number=ord_info["code"],
                user_id=cashier.id,
                table_number=ord_info["channel"],
                order_type=ord_info["type"],
                status=ord_info["status"],
                subtotal=subtotal,
                discount_amount=ord_info["discount"],
                tax_amount=0,
                total_amount=total_amount,
                note=f"Đơn hàng demo {ord_info['channel']}",
                created_at=created_time,
                updated_at=created_time,
            )
            order.items = order_items_to_add
            db.add(order)
            db.flush()

            # Add payment record
            payment = Payment(
                order_id=order.id,
                user_id=cashier.id,
                amount=total_amount,
                payment_method=PaymentMethod.CASH,
                status=PaymentStatus.SUCCESS,
                transaction_code=f"TXN-{ord_info['code']}",
                created_at=created_time,
            )
            db.add(payment)

    db.commit()
    logger.info("Database seeding completed successfully!")
