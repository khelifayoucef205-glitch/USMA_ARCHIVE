from flask import Blueprint, render_template
from app.database import get_db_connection
from datetime import datetime

player = Blueprint("player", __name__)


def get_player_status(player_data):

    # تحقق من الوفاة
    if player_data.get('Person_death_date'):
        return 'deceased'
    
    # تحقق من النشاط
    if not player_data.get('Is_Active'):
        return 'retired'
    
    # تحقق من USMA الحالي
    if player_data.get('usma_current'):
        return 'active_with_usma'
    
    # إذا كان نشطاً لكن ليس مع USMA
    if player_data.get('usma_history'):
        return 'former_usma'
    
    # نشط لكن لا تاريخ مع USMA
    return 'active_no_club'


def format_date(date):
    """تنسيق التاريخ"""
    if not date:
        return None
    if isinstance(date, str):
        return date
    return date.strftime('%Y-%m-%d')


def calculate_age(birth_date, death_date=None):
    """حساب العمر"""
    if not birth_date:
        return None
    
    reference_date = death_date if death_date else datetime.now().date()
    age = reference_date.year - birth_date.year
    
    if isinstance(birth_date, str):
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    if isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d').date()
    
    return age


@player.route("/player/<int:player_id>")
def player_page(player_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # 1. بيانات اللاعب الأساسية
    cursor.execute("""
        SELECT
            p.Person_id,
            p.Person_First_Name,
            p.Person_Last_Name,
            p.Person_Display_Name,
            p.Person_First_Name_ar,
            p.Person_Last_Name_ar,
            p.Person_Display_Name_ar,
            p.Person_birth_date,
            p.Person_death_date,
            p.Sex,
            c.Country_Name,
            c.Country_Name_ar,
            
            pl.Player_id,
            pl.Player_Nickname,
            pl.Player_Nickname_ar,
            pl.Is_Active

        FROM Player pl
        JOIN Person p ON pl.Person_id = p.Person_id
        JOIN Country c ON p.Country_id = c.Country_id
        WHERE pl.Player_id = %s
    """, (player_id,))

    player_data = cursor.fetchone()

    if player_data is None:
        cursor.close()
        connection.close()
        return "Player not found", 404

    # 2. المواضع
    cursor.execute("""
        SELECT
            po.Position_id,
            po.Position_Code,
            po.Position_Name,
            po.Position_Name_ar,
            pc.Category_Name,
            pc.Category_Name_ar,
            pp.Is_Main

        FROM Player_Position pp
        JOIN Position po ON pp.Position_id = po.Position_id
        JOIN Position_Category pc ON po.Position_Category_id = pc.Position_Category_id
        WHERE pp.Player_id = %s
        ORDER BY pp.Is_Main DESC, po.Position_id
    """, (player_id,))

    positions = cursor.fetchall()

    # 3. بيانات USMA الحالية والسابقة
    cursor.execute("""
        SELECT
            pc.Club_id,
            c.Club_Current_Name,
            c.Club_Short_Name,
            pc.Join_Date,
            pc.Leave_Date,
            pc.Is_Actual

        FROM Player_Club pc
        JOIN Club c ON pc.Club_id = c.Club_id
        WHERE pc.Player_id = %s 
          AND c.Club_id = 1
        ORDER BY pc.Join_Date DESC
    """, (player_id,))

    usma_records = cursor.fetchall()

    usma_current = None
    usma_history = []
    
    for record in usma_records:
    
        is_current = (
            record['Is_Actual'] == 1
            and record['Leave_Date'] is None
        )
    
        if is_current:
            if usma_current is None:
                usma_current = record
            else:
                # توجد أكثر من فترة حالية
                # نضع الأقدم في التاريخ بدلاً من فقدانها
                usma_history.append(record)
        else:
            usma_history.append(record)
    # 4. مواسم USMA
    cursor.execute("""
        SELECT
            ps.Season_Number,
            s.Season_Name,
            s.Start_Year,
            s.End_Year,
            po.Position_Code,
            po.Position_Name,
            po.Position_Name_ar,
            ps.Jersey_Number

        FROM Player_Season ps
        JOIN Season s ON ps.Season_Number = s.Season_Number
        JOIN Position po ON ps.Position_id = po.Position_id
        WHERE ps.Player_id = %s 
          AND ps.Club_id = 1
        ORDER BY s.Start_Year DESC
    """, (player_id,))

    usma_seasons = cursor.fetchall()

    # 5. جميع الأندية الأخرى
    cursor.execute("""
        SELECT
            pc.Club_id,
            c.Club_Current_Name,
            c.Club_Short_Name,
            ci.City_Name,
            pc.Join_Date,
            pc.Leave_Date,
            pc.Is_Actual

        FROM Player_Club pc
        JOIN Club c ON pc.Club_id = c.Club_id
        LEFT JOIN City ci ON c.City_id = ci.City_id
        WHERE pc.Player_id = %s 
          AND c.Club_id != 1
        ORDER BY pc.Join_Date DESC
    """, (player_id,))

    other_clubs = cursor.fetchall()

    cursor.close()
    connection.close()

    # تحضير البيانات
    player_data['usma_current'] = usma_current
    player_data['usma_history'] = usma_history
    player_status = get_player_status(player_data)
    
    # حساب العمر
    player_data['age'] = calculate_age(
        player_data['Person_birth_date'],
        player_data['Person_death_date']
    )

    return render_template(
        "player.html",
        Title=player_data["Person_Display_Name"],
        player=player_data,
        positions=positions,
        usma_current=usma_current,
        usma_history=usma_history,
        usma_seasons=usma_seasons,
        other_clubs=other_clubs,
        player_status=player_status
    )