CREATE DATABASE USMA1937_db;

USE USMA1937_db;

ALTER DATABASE USMA1937_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Continent (
    Continent_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Continent_Name VARCHAR(50) NOT NULL,
    Continent_Name_ar VARCHAR(50) NOT NULL
);

ALTER TABLE Continent
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Country (
    Country_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    ISO_Alpha2 VARCHAR(2) NOT NULL UNIQUE,
    Country_Name VARCHAR(100) NOT NULL,
    Country_Name_ar VARCHAR(100) NOT NULL,
    ISO_Alpha3 VARCHAR(3) NOT NULL UNIQUE,
    Country_Code VARCHAR(4) NOT NULL,
    Continent_id INT NOT NULL,   
    FOREIGN KEY (Continent_id) REFERENCES Continent(Continent_id)
);

ALTER TABLE Country
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE City (
    City_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    City_Name VARCHAR(100) NOT NULL,
    City_Name_ar VARCHAR(100) NOT NULL,
    Country_id INT NOT NULL,
    FOREIGN KEY (Country_id) REFERENCES Country(Country_id)
);

ALTER TABLE City
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Position_Category (
    Position_Category_id INT PRIMARY KEY AUTO_INCREMENT,
    Category_Name VARCHAR(50) NOT NULL UNIQUE,
    Category_Name_ar VARCHAR(50) NOT NULL UNIQUE
);

ALTER TABLE Position_Category
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Position (
    Position_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Position_Category_id INT NOT NULL,
    Position_Code VARCHAR(5) NOT NULL UNIQUE,
    Position_Name VARCHAR(50) NOT NULL,
    Position_Name_ar VARCHAR(50),
    FOREIGN KEY (Position_Category_id) REFERENCES Position_Category(Position_Category_id)
);

ALTER TABLE Position
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Person (
    Person_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Person_First_Name VARCHAR(100),
    Person_Last_Name VARCHAR(100),
    Person_Display_Name VARCHAR(200) NOT NULL,
    Person_First_Name_ar VARCHAR(100),
    Person_Last_Name_ar VARCHAR(100),
    Person_Display_Name_ar VARCHAR(200),
    Person_birth_date DATE,
    Sex ENUM('Male', 'Female') DEFAULT 'Male',
    Country_id INT NOT NULL,
    FOREIGN KEY (Country_id) REFERENCES Country (Country_id)
);

ALTER TABLE Person
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Player (
    Player_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Person_id INT NOT NULL UNIQUE,
    Player_Nickname VARCHAR(100),
    Player_Nickname_ar VARCHAR(100),
    Main_Jersey_Number SMALLINT,
    Is_Active BOOLEAN DEFAULT 1,
    FOREIGN KEY (Person_id) REFERENCES Person (Person_id)
);

CREATE TABLE Referee (
    Referee_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Person_id INT NOT NULL UNIQUE,
    FOREIGN KEY (Person_id) REFERENCES Person (Person_id)
);

CREATE TABLE Staff_Member (
    Staff_Member_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Person_id INT NOT NULL UNIQUE,
    Role ENUM('Manager', 'Assistant Coach', 'Goalkeeper Coach', 'Physical Coach', 'Doctor', 'Other'),
    Specialty VARCHAR(100),
    FOREIGN KEY (Person_id) REFERENCES Person (Person_id)
);

CREATE TABLE Player_Position (
    Player_id INT NOT NULL,
    Position_id INT NOT NULL,
    Is_Main BOOLEAN DEFAULT 0,
    PRIMARY KEY (Player_id, Position_id),
    FOREIGN KEY (Player_id) REFERENCES Player(Player_id),
    FOREIGN KEY (Position_id) REFERENCES `Position` (Position_id)
);

CREATE TABLE Club (
    Club_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Club_Current_Name VARCHAR(100) NOT NULL,
    Club_Short_Name VARCHAR(10) NOT NULL,
    City_id INT NOT NULL,
    Club_Founding_Date DATE,
    Dissolution_Date DATE,
    Club_Status ENUM('Active', 'Inactive', 'Dissolved', 'Suspended') DEFAULT 'Active',
    FOREIGN KEY (City_id) REFERENCES City (City_id)
);

CREATE TABLE Club_History_Names (
    Club_history_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    Club_id INT NOT NULL,
    Club_Name VARCHAR(100) NOT NULL,
    Language_Code VARCHAR (3),
    Start_Year SMALLINT,
    End_Year SMALLINT,
    Is_Actual BOOLEAN DEFAULT 1,
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id)
);

ALTER TABLE Club_History_Names
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Stadium (
    Stadium_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    Stadium_Current_Name VARCHAR(100) NOT NULL,
    Stadium_Capacity INT,
    Stadium_Founding_Date DATE,
    City_id INT NOT NULL,
    FOREIGN KEY (City_id) REFERENCES City (City_id)    
);

CREATE TABLE Stadium_History_Names (
    Stadium_history_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    Stadium_id INT NOT NULL,
    Stadium_Name VARCHAR(100) NOT NULL,
    Language_Code VARCHAR (3),
    Start_Year SMALLINT,
    End_Year SMALLINT,
    Is_Actual BOOLEAN DEFAULT 1,
    FOREIGN KEY (Stadium_id) REFERENCES Stadium (Stadium_id)
);

ALTER TABLE Stadium_History_Names
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Player_Club (
    Player_id INT NOT NULL,
    Club_id INT NOT NULL,
    Join_Date DATE,
    Leave_Date DATE,
    Is_Actual BOOLEAN DEFAULT 1,
    PRIMARY KEY (Player_id, Club_id, Join_Date),
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id),
    FOREIGN KEY (Player_id) REFERENCES Player (Player_id)
);

CREATE TABLE Season (
    Season_Number INT NOT NULL PRIMARY KEY,
    Season_Name VARCHAR(9) NOT NULL,
    Start_Year SMALLINT,
    End_Year SMALLINT
);

CREATE TABLE Player_Season (
    Player_id INT NOT NULL,
    Club_id INT NOT NULL,
    Season_Number INT NOT NULL,
    Position_id INT NOT NULL,
    Jersey_Number INT DEFAULT NULL,
    PRIMARY KEY (Player_id, Club_id, Season_Number),
    FOREIGN KEY (Player_id) REFERENCES Player(Player_id),
    FOREIGN KEY (Club_id) REFERENCES Club(Club_id),
    FOREIGN KEY (Season_Number) REFERENCES Season(Season_Number),
    FOREIGN KEY (Position_id) REFERENCES Position(Position_id)
);

CREATE TABLE Main_Stadium (
    Stadium_id INT NOT NULL,
    Club_id INT NOT NULL,
    Start_Year SMALLINT,
    End_Year SMALLINT,
    Is_Actual BOOLEAN DEFAULT 1,
    PRIMARY KEY (Stadium_id, Club_id, Start_Year),
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id),
    FOREIGN KEY (Stadium_id) REFERENCES Stadium (Stadium_id)
);

CREATE TABLE Competition (
    Competition_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Competition_Name VARCHAR(100) NOT NULL,
    Competition_Name_ar VARCHAR(100) NOT NULL,
    Competition_Type ENUM ('Local', 'Regional', 'Continental', 'International'),
    Competition_Format ENUM ('League' , 'Cup', 'Group + Knockout')
);

ALTER TABLE Competition
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE TABLE Competition_Stage (
    Stage_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Competition_id INT NOT NULL,
    Season_Number INT NOT NULL,
    Stage_Name VARCHAR(50) NOT NULL,
    Stage_Name_ar VARCHAR(50),
    Stage_Level SMALLINT NOT NULL,
    Stage_Type ENUM('Qualification', 'Group', 'Knockout', 'Final') NOT NULL,
    Stage_Format ENUM('Single Match', 'Two Legs', 'League Table', 'Groups', 'Swiss'),
    FOREIGN KEY (Season_Number) REFERENCES Season(Season_Number),
    FOREIGN KEY (Competition_id) REFERENCES Competition(Competition_id)
);

ALTER TABLE Competition_Stage
CONVERT TO CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

/*CREATE TABLE Player_Season (
    Player_id INT NOT NULL,
    Season_Number INT NOT NULL,
    PRIMARY KEY (Player_id, Season_Number),
    FOREIGN KEY (Season_Number) REFERENCES Season (Season_Number),
    FOREIGN KEY (Player_id) REFERENCES Player (Player_id)
);*/

/*CREATE TABLE Club_Season (
    Club_id INT NOT NULL,
    Season_Number INT NOT NULL,
    PRIMARY KEY (Club_id, Season_Number)
    FOREIGN KEY (Season_Number) REFERENCES Season (Season_Number),
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id)
);*/

CREATE TABLE Competition_Season (
    Competition_id INT NOT NULL,
    Season_Number INT NOT NULL,
    Competition_Start_Date DATE,
    Competition_End_Date DATE,
    Competition_Winner_Club_id INT,
    PRIMARY KEY (Competition_id, Season_Number),
    FOREIGN KEY (Season_Number) REFERENCES Season (Season_Number),
    FOREIGN KEY (Competition_id) REFERENCES Competition (Competition_id),
    FOREIGN KEY (Competition_Winner_Club_id) REFERENCES Club (Club_id)
);

CREATE TABLE Competition_Club (
    Competition_id INT NOT NULL,
    Club_id INT NOT NULL,
    Season_Number INT NOT NULL,
    Club_Final_Stage INT NOT NULL,
    /*Is_Winner boolean DEFAULT 0,*/
    PRIMARY KEY (Competition_id, Season_Number, Club_id),
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id),
    FOREIGN KEY (Club_Final_Stage) REFERENCES Competition_Stage (Stage_id),
    FOREIGN KEY (Competition_id, Season_Number) REFERENCES Competition_Season (Competition_id, Season_Number)
);

CREATE TABLE Formation (
    Formation_id INT PRIMARY KEY AUTO_INCREMENT,
    Formation_Base VARCHAR(10) NOT NULL,
    Formation_Variant ENUM('Flat', 'Diamond', 'Double Pivot', 'Offensive', 'Defensive', 'Libero'),
    UNIQUE(Formation_Base, Formation_Variant)
);

CREATE TABLE Football_Match (
    Football_Match_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Football_Match_Date DATE,
    Football_Match_Status ENUM('Scheduled', 'Live', 'Half-Time', 'Full-Time', 'Unknown') DEFAULT 'Scheduled',
    Football_Match_State ENUM('Normal', 'Postponed', 'Cancelled', 'Abandoned', 'Awarded') DEFAULT 'Normal',
    Opponent_Club_id INT NOT NULL,
    USMA_Formation_id INT,
    Is_Home BOOLEAN DEFAULT 0,
    USMA_Score INT,
    Opponent_Score INT,
    Went_To_Penalties BOOLEAN DEFAULT 0,
    USMA_Penalties_Score INT DEFAULT NULL,
    Opponent_Penalties_Score INT DEFAULT NULL,
    Stadium_id INT,
    Is_Neutral BOOLEAN DEFAULT 0,
    Season_Number INT NOT NULL,
    Competition_id INT NOT NULL,
    Stage_id INT NOT NULL,
    FOREIGN KEY (Opponent_Club_id) REFERENCES Club (Club_id),
    FOREIGN KEY (Season_Number) REFERENCES Season (Season_Number),
    FOREIGN KEY (Competition_id) REFERENCES Competition (Competition_id),
    FOREIGN KEY (Stage_id) REFERENCES Competition_Stage (Stage_id),
    FOREIGN KEY (Stadium_id) REFERENCES Stadium (Stadium_id),
    FOREIGN KEY (USMA_Formation_id) REFERENCES Formation (Formation_id)
);

CREATE TABLE Lineup (
    Football_Match_id INT NOT NULL,
    Club_id INT NOT NULL,
    Player_id INT NOT NULL,
    Position_id INT,
    Formation_Slot VARCHAR(10), 
    Is_Starter BOOLEAN DEFAULT 0,
    Is_Captain BOOLEAN DEFAULT 0,
    Jersey_Number SMALLINT, 
    Minute_In SMALLINT,
    Minute_Out SMALLINT, 
    PRIMARY KEY (Football_Match_id, Club_id, Player_id),
    FOREIGN KEY (Football_Match_id) REFERENCES Football_Match(Football_Match_id),
    FOREIGN KEY (Club_id) REFERENCES Club(Club_id),
    FOREIGN KEY (Player_id) REFERENCES Player(Player_id),
    FOREIGN KEY (Position_id) REFERENCES Position (Position_id)
);

CREATE TABLE Event (
    Event_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Football_Match_id INT NOT NULL,
    Event_Type ENUM('Goal', 'Penalty', 'Card', 'Substitution') NOT NULL,
    Event_Half ENUM('1st-Half', '2nd-Half', 'Extra-Time-1st-Half', 'Extra-Time-2nd-Half', 'Penalty Shootout'),
    Event_Minutes SMALLINT,
    Added_Minute SMALLINT,
    FOREIGN KEY (Football_Match_id) REFERENCES Football_Match (Football_Match_id) ON DELETE CASCADE
);

CREATE TABLE Penalty (
    Penalty_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Event_id INT NOT NULL UNIQUE,
    Referee_id INT NOT NULL,
    Penalty_Taker_Player_id INT NOT NULL,
    Defending_Goalkeeper_Player_id INT NOT NULL,
    Player_Earned_Penalty_id INT,  -- Player who was fouled/earned the penalty
    Player_Conceded_Penalty_id INT NOT NULL,  -- Player who committed the foul
    Penalty_Outcome ENUM('Scored', 'Missed', 'Saved') NOT NULL,
    FOREIGN KEY (Event_id) REFERENCES Event (Event_id) ON DELETE CASCADE,
    FOREIGN KEY (Referee_id) REFERENCES Referee (Referee_id) ON DELETE CASCADE,
    FOREIGN KEY (Penalty_Taker_Player_id) REFERENCES Player (Player_id),
    FOREIGN KEY (Defending_Goalkeeper_Player_id) REFERENCES Player (Player_id),
    FOREIGN KEY (Player_Earned_Penalty_id) REFERENCES Player (Player_id) ON DELETE SET NULL,
    FOREIGN KEY (Player_Conceded_Penalty_id) REFERENCES Player (Player_id)
);

CREATE TABLE Goal (
    Goal_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Event_id INT NOT NULL UNIQUE,
    Goal_Type VARCHAR(100),
    Is_Own_Goal BOOLEAN DEFAULT 0,
    Is_Disallowed BOOLEAN DEFAULT 0,
    Disallowed_Reason VARCHAR(100),
    Club_id INT NOT NULL,
    Goalscorer_Player_id INT NOT NULL,
    Assist_Player_id INT,
    Penalty_id INT,
    FOREIGN KEY (Penalty_id) REFERENCES Penalty (Penalty_id),
    FOREIGN KEY (Event_id) REFERENCES Event (Event_id) ON DELETE CASCADE,
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id),
    FOREIGN KEY (Goalscorer_Player_id) REFERENCES Player (Player_id),
    FOREIGN KEY (Assist_Player_id) REFERENCES Player (Player_id) ON DELETE SET NULL
);

CREATE TABLE Card (
    Card_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Event_id INT NOT NULL UNIQUE,
    Referee_id INT NOT NULL,
    Player_id INT NOT NULL, 
    Card_Type ENUM('Yellow', 'Red') NOT NULL,
    Reason VARCHAR(200),
    FOREIGN KEY (Event_id) REFERENCES Event (Event_id) ON DELETE CASCADE,
    FOREIGN KEY (Referee_id) REFERENCES Referee (Referee_id) ON DELETE CASCADE,
    FOREIGN KEY (Player_id) REFERENCES Player (Player_id) ON DELETE CASCADE
);

CREATE TABLE Substitution (
    Substitution_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Event_id INT NOT NULL UNIQUE,
    Staff_Member_id INT NOT NULL,  -- Coach/Manager who made the sub
    Player_Out_id INT NOT NULL,
    Player_In_id INT NOT NULL,
    FOREIGN KEY (Event_id) REFERENCES Event (Event_id) ON DELETE CASCADE,
    FOREIGN KEY (Staff_Member_id) REFERENCES Staff_Member (Staff_Member_id) ON DELETE CASCADE,
    FOREIGN KEY (Player_Out_id) REFERENCES Player (Player_id) ON DELETE CASCADE,
    FOREIGN KEY (Player_In_id) REFERENCES Player (Player_id) ON DELETE CASCADE
);

CREATE TABLE Referee_Staff (
    Referee_id INT NOT NULL,
    Football_Match_id INT NOT NULL,
    Referee_Role ENUM ('Center Referee', 'Assistant Referee', 'Fourth Official', 'VAR Referee', 'Assistant VAR Referee'),
    PRIMARY KEY (Referee_id, Football_Match_id),
    UNIQUE KEY unique_role_per_match (Football_Match_id, Referee_Role),
    FOREIGN KEY (Football_Match_id) REFERENCES Football_Match (Football_Match_id) ON DELETE CASCADE,
    FOREIGN KEY (Referee_id) REFERENCES Referee (Referee_id) ON DELETE CASCADE
);

CREATE TABLE Employment (
    Staff_Member_id INT NOT NULL,
    Club_id INT NOT NULL,
    Join_Date DATE,
    Leave_Date DATE,
    Is_Actual BOOLEAN DEFAULT 1,
    PRIMARY KEY (Staff_Member_id, Club_id, Join_Date),
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id),
    FOREIGN KEY (Staff_Member_id) REFERENCES Staff_Member (Staff_Member_id)
);

CREATE TABLE Staff_Member_Football_Match (
    Staff_Member_id INT NOT NULL,
    Football_Match_id INT NOT NULL,
    Role_In_Match VARCHAR(100),
    Is_On_Bench BOOLEAN,
    Club_id INT NOT NULL,
    PRIMARY KEY (Staff_Member_id, Football_Match_id),
    FOREIGN KEY (Staff_Member_id) REFERENCES Staff_Member (Staff_Member_id),
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id),
    FOREIGN KEY (Football_Match_id) REFERENCES Football_Match (Football_Match_id)
);

CREATE TABLE Player_Season_Stats (
    Player_id INT NOT NULL,
    Season_Number INT NOT NULL,
    Club_id INT NOT NULL,
    Goals INT DEFAULT 0,
    Assists INT DEFAULT 0,
    Yellow_Cards INT DEFAULT 0,
    Red_Cards INT DEFAULT 0,
    Matches_Played INT DEFAULT 0,
    Minutes_Played INT DEFAULT 0,
    PRIMARY KEY (Player_id, Season_Number, Club_id),
    FOREIGN KEY (Player_id) REFERENCES Player (Player_id),
    FOREIGN KEY (Season_Number) REFERENCES Season (Season_Number),
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id)
);

CREATE TABLE League_Table (
    Competition_id INT NOT NULL,
    Season_Number INT NOT NULL,
    Club_id INT NOT NULL,
    Position INT,
    Matches_Played INT,
    Wins INT,
    Draws INT,
    Losses INT,
    Goals_For INT,
    Goals_Against INT,
    Goal_Difference INT,
    Points INT,
    PRIMARY KEY (Competition_id, Season_Number, Club_id),
    FOREIGN KEY (Competition_id, Season_Number) REFERENCES Competition_Season (Competition_id, Season_Number),
    FOREIGN KEY (Club_id) REFERENCES Club (Club_id)
);

ALTER TABLE Player_Club ADD CONSTRAINT chk_active_club 
CHECK (Is_Actual = 0 OR (Join_Date IS NOT NULL AND Leave_Date IS NULL));

CREATE TABLE Suspension (
    Suspension_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Player_id INT NOT NULL,
    Suspension_Reason ENUM('Red Card', 'Accumulation (Yellow Cards)', 'Foul Play', 'Misconduct', 'Other') NOT NULL,
    Suspension_Start_Date DATE NOT NULL,
    Suspension_End_Date DATE,
    Matches_Count INT NOT NULL, 
    Fine_Amount DECIMAL(10, 2),
    Is_Serving BOOLEAN DEFAULT 1,
    Is_In_Match BOOLEAN DEFAULT 0,
    Football_Match_id INT,
    Notes VARCHAR(500),
    Created_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Player_id) REFERENCES Player (Player_id) ON DELETE CASCADE,
    FOREIGN KEY (Football_Match_id) REFERENCES Football_Match(Football_Match_id)
);

CREATE TABLE Injury (
    Injury_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Player_id INT NOT NULL,
    Injury_Type ENUM('Muscle Strain', 'Sprain', 'Fracture', 'Dislocation', 'Laceration', 'Concussion', 'Other') NOT NULL,
    Body_Part ENUM('Head', 'Neck', 'Shoulder', 'Arm', 'Elbow', 'Wrist', 'Hand', 'Chest', 'Back', 'Hip', 'Thigh', 'Knee', 'Calf', 'Ankle', 'Foot', 'Other') NOT NULL,
    Severity ENUM('Minor', 'Moderate', 'Severe', 'Critical') NOT NULL,
    Injury_Date DATE NOT NULL,
    Recovery_Date DATE,
    Is_Active BOOLEAN DEFAULT 1,  -- هل الإصابة لا تزال نافذة؟
    Notes VARCHAR(500),
    Is_In_Match BOOLEAN DEFAULT 0,
    Football_Match_id INT, 
    FOREIGN KEY (Player_id) REFERENCES Player (Player_id) ON DELETE CASCADE,
    FOREIGN KEY (Football_Match_id) REFERENCES Football_Match(Football_Match_id)
);

CREATE TABLE Event_Suspension (
    Event_Suspension_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Event_id INT NOT NULL,
    Suspension_id INT NOT NULL,
    Suspension_Triggered_Date DATE NOT NULL,  -- متى بدأت التوقيفة
    UNIQUE KEY unique_event_suspension (Event_id, Suspension_id),
    FOREIGN KEY (Event_id) REFERENCES Event (Event_id) ON DELETE CASCADE,
    FOREIGN KEY (Suspension_id) REFERENCES Suspension (Suspension_id) ON DELETE CASCADE
);

CREATE TABLE Event_Injury (
    Event_Injury_id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    Event_id INT NOT NULL,
    Injury_id INT NOT NULL,
    Injury_Occurred_Date DATE NOT NULL,  -- متى حدثت الإصابة
    UNIQUE KEY unique_event_injury (Event_id, Injury_id),
    FOREIGN KEY (Event_id) REFERENCES Event (Event_id) ON DELETE CASCADE,
    FOREIGN KEY (Injury_id) REFERENCES Injury (Injury_id) ON DELETE CASCADE
);


-- ============================================================================
-- USMA DATABASE CONSTRAINTS & TRIGGERS
-- ============================================================================
-- هذا الملف يحتوي على قيود منطقية وتريجرز لضمان جودة البيانات
-- ============================================================================

-- ============================================================================
-- USMA DATABASE CONSTRAINTS & TRIGGERS
-- ============================================================================
-- هذا الملف يحتوي على قيود منطقية وتريجرز لضمان جودة البيانات
-- ============================================================================

USE USMA1937_db;

-- ============================================================================
-- ============ 1. CHECK CONSTRAINTS ==============
-- ============================================================================

-- 1.1: Opponent_Club_id يجب أن يكون دائماً ≠ 1 (USMA)
ALTER TABLE Football_Match
ADD CONSTRAINT chk_opponent_not_usma 
CHECK (Opponent_Club_id != 1);

-- 1.2: Player_In_id ≠ Player_Out_id في التبديل
ALTER TABLE Substitution
ADD CONSTRAINT chk_different_players_substitution 
CHECK (Player_Out_id != Player_In_id);

-- 1.3: درجات الفريق لا يمكن أن تكون سالبة
ALTER TABLE Football_Match
ADD CONSTRAINT chk_usma_score_non_negative 
CHECK (USMA_Score >= 0);

ALTER TABLE Football_Match
ADD CONSTRAINT chk_opponent_score_non_negative 
CHECK (Opponent_Score >= 0);

-- 1.4: درجات الركلات الترجيحية لا تكون سالبة
ALTER TABLE Football_Match
ADD CONSTRAINT chk_usma_penalties_non_negative 
CHECK (USMA_Penalties_Score >= 0);

ALTER TABLE Football_Match
ADD CONSTRAINT chk_opponent_penalties_non_negative 
CHECK (Opponent_Penalties_Score >= 0);

-- 1.5: إذا ذهبت المباراة للركلات ترجيحية، يجب أن تكون النتيجة متساوية في وقت النهاية العادية
ALTER TABLE Football_Match
ADD CONSTRAINT chk_penalties_requires_draw 
CHECK (Went_To_Penalties = 0 OR USMA_Score = Opponent_Score);

-- 1.6: رقم الدقيقة يجب أن يكون موجب أو 0
ALTER TABLE Event
ADD CONSTRAINT chk_event_minutes_non_negative 
CHECK (Event_Minutes >= 0);

-- 1.7: Jersey Number في Lineup يجب أن يكون بين 1 و 99
ALTER TABLE Lineup
ADD CONSTRAINT chk_jersey_number_valid 
CHECK (Jersey_Number > 0 AND Jersey_Number <= 99);

-- 1.8: Player_id يجب أن يختلف عن Assist_Player_id في Goal (لا يمكن لاعب أن يسجل ويصنع لنفسه)
ALTER TABLE Goal
ADD CONSTRAINT chk_different_scorer_and_assist 
CHECK (Goalscorer_Player_id != Assist_Player_id);

-- 1.9: Minute_Out يجب أن يكون أكبر من Minute_In في Lineup
ALTER TABLE Lineup
ADD CONSTRAINT chk_minute_in_before_minute_out 
CHECK (Minute_In <= Minute_Out OR Minute_Out IS NULL);

-- 1.10: تاريخ الإصابة يجب أن يكون قبل تاريخ الشفاء
ALTER TABLE Injury
ADD CONSTRAINT chk_recovery_after_injury 
CHECK (Recovery_Date IS NULL OR Injury_Date <= Recovery_Date);

-- 1.11: تاريخ انتهاء التوقيف يجب أن يكون بعد البداية
ALTER TABLE Suspension
ADD CONSTRAINT chk_suspension_end_after_start 
CHECK (Suspension_End_Date IS NULL OR Suspension_Start_Date <= Suspension_End_Date);

-- ============================================================================
-- ============ 2. TRIGGERS FOR COMPLEX VALIDATIONS ==============
-- ============================================================================

-- ============================================================================
-- TRIGGER 2.1: التحقق من أن اللاعب مسجل مع الفريق (Is_Actual = 1) عند إضافته في Lineup
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_validate_player_active_before_lineup
BEFORE INSERT ON Lineup
FOR EACH ROW
BEGIN
    DECLARE player_active INT;
    DECLARE error_message VARCHAR(255);
    
    -- التحقق من أن اللاعب مسجل مع الفريق وعقده نشط
    SELECT COUNT(*) INTO player_active
    FROM Player_Club
    WHERE Player_id = NEW.Player_id 
      AND Club_id = NEW.Club_id
      AND Is_Actual = 1;
    
    IF player_active = 0 THEN
        SET error_message = CONCAT(
            'خطأ: اللاعب #', NEW.Player_id, 
            ' غير مسجل مع الفريق #', NEW.Club_id, 
            ' أو عقده منتهي'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.2: التحقق من أن تاريخ المباراة يقع ضمن فترة عقد اللاعب
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_validate_player_contract_date
BEFORE INSERT ON Lineup
FOR EACH ROW
BEGIN
    DECLARE match_date DATE;
    DECLARE join_date DATE;
    DECLARE leave_date DATE;
    DECLARE error_message VARCHAR(255);
    
    -- الحصول على تاريخ المباراة
    SELECT Football_Match_Date INTO match_date
    FROM Football_Match
    WHERE Football_Match_id = NEW.Football_Match_id;
    
    -- الحصول على فترة عقد اللاعب مع الفريق
    SELECT Join_Date, Leave_Date INTO join_date, leave_date
    FROM Player_Club
    WHERE Player_id = NEW.Player_id 
      AND Club_id = NEW.Club_id
      AND Is_Actual = 1
    ORDER BY Join_Date DESC
    LIMIT 1;
    
    -- التحقق من أن المباراة تقع ضمن فترة العقد
    IF match_date < join_date OR (leave_date IS NOT NULL AND match_date > leave_date) THEN
        SET error_message = CONCAT(
            'خطأ: تاريخ المباراة (', match_date, ') خارج فترة عقد اللاعب #', 
            NEW.Player_id, ' من ', join_date, ' إلى ', 
            COALESCE(leave_date, 'الآن')
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.3: اللاعب المطرود بـ Red Card لا يمكنه الظهور بعده في نفس المباراة
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_prevent_events_after_red_card
BEFORE INSERT ON Event
FOR EACH ROW
BEGIN
    DECLARE red_card_minute INT;
    DECLARE player_is_red_carded INT;
    DECLARE error_message VARCHAR(255);
    
    -- إذا كان الحدث يتعلق بـ Goal
    IF NEW.Event_Type = 'Goal' THEN
        -- التحقق من أن الهداف لم يكن مطروداً قبل هذه اللحظة
        SELECT COUNT(*) INTO player_is_red_carded
        FROM Card
        JOIN Event ON Card.Event_id = Event.Event_id
        WHERE Event.Football_Match_id = NEW.Football_Match_id
          AND Card.Card_Type = 'Red'
          AND Card.Player_id = (
              SELECT Goalscorer_Player_id 
              FROM Goal 
              WHERE Goal.Event_id = NEW.Event_id
          )
          AND Event.Event_Minutes <= NEW.Event_Minutes;
        
        IF player_is_red_carded > 0 THEN
            SET error_message = 'خطأ: لاعب مطرود لا يمكنه تسجيل أهداف';
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
        END IF;
    END IF;
    
    -- إذا كان الحدث يتعلق بـ Substitution (تبديل)
    IF NEW.Event_Type = 'Substitution' THEN
        SELECT COUNT(*) INTO player_is_red_carded
        FROM Card
        JOIN Event ON Card.Event_id = Event.Event_id
        WHERE Event.Football_Match_id = NEW.Football_Match_id
          AND Card.Card_Type = 'Red'
          AND Card.Player_id = (
              SELECT Player_In_id 
              FROM Substitution 
              WHERE Substitution.Event_id = NEW.Event_id
          )
          AND Event.Event_Minutes <= NEW.Event_Minutes;
        
        IF player_is_red_carded > 0 THEN
            SET error_message = 'خطأ: لاعب مطرود لا يمكنه الدخول للملعب';
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
        END IF;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.4: لاعب لا يعود للملعب بعد خروجه في تبديل (نفس المباراة)
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_prevent_player_reentry_after_substitution
BEFORE INSERT ON Lineup
FOR EACH ROW
BEGIN
    DECLARE player_out_minute INT;
    DECLARE error_message VARCHAR(255);
    
    -- التحقق من أن اللاعب لم يكن قد خرج من الملعب سابقاً
    SELECT MAX(Event_Minutes) INTO player_out_minute
    FROM Substitution
    JOIN Event ON Substitution.Event_id = Event.Event_id
    WHERE Event.Football_Match_id = NEW.Football_Match_id
      AND Substitution.Player_Out_id = NEW.Player_id
      AND Event.Event_Minutes <= COALESCE(NEW.Minute_In, 120);
    
    IF player_out_minute IS NOT NULL THEN
        SET error_message = CONCAT(
            'خطأ: اللاعب #', NEW.Player_id, 
            ' خرج من الملعب في الدقيقة ', player_out_minute, 
            ' ولا يمكنه العودة في نفس المباراة'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.5: التحقق من Player_In_id و Player_Out_id مختلفان في Substitution
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_validate_substitution_players
BEFORE INSERT ON Substitution
FOR EACH ROW
BEGIN
    DECLARE error_message VARCHAR(255);
    
    IF NEW.Player_Out_id = NEW.Player_In_id THEN
        SET error_message = 'خطأ: اللاعب الخارج واللاعب الداخل يجب أن يكونا مختلفان';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.6: حارس المرمى الدفاع يجب أن يكون من الفريق الصحيح
--              إذا ضرب USMA → حارس من الخصم
--              إذا ضرب الخصم → حارس من USMA
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_validate_goalkeeper_in_penalty
BEFORE INSERT ON Penalty
FOR EACH ROW
BEGIN
    DECLARE goalkeeper_count INT;
    DECLARE goalkeeper_club_id INT;
    DECLARE penalty_taker_club_id INT;
    DECLARE match_opponent_club_id INT;
    DECLARE error_message VARCHAR(255);
    DECLARE match_id INT;
    DECLARE expected_goalkeeper_club INT;
    
    -- الحصول على معرف المباراة من Event
    SELECT Football_Match_id INTO match_id
    FROM Event 
    WHERE Event_id = NEW.Event_id;
    
    -- الحصول على فريق الخصم من المباراة
    SELECT Opponent_Club_id INTO match_opponent_club_id
    FROM Football_Match
    WHERE Football_Match_id = match_id;
    
    -- الحصول على فريق ضارب الجزاء
    SELECT Club_id INTO penalty_taker_club_id
    FROM Lineup
    WHERE Football_Match_id = match_id
      AND Player_id = NEW.Penalty_Taker_Player_id;
    
    -- التحقق من أن حارس المرمى الدفاع موجود في الـ Lineup
    SELECT COUNT(*) INTO goalkeeper_count
    FROM Lineup
    WHERE Football_Match_id = match_id
      AND Player_id = NEW.Defending_Goalkeeper_Player_id;
    
    IF goalkeeper_count = 0 THEN
        SET error_message = CONCAT(
            'خطأ: حارس المرمى #', NEW.Defending_Goalkeeper_Player_id,
            ' لم يشارك في المباراة'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
    
    -- الحصول على فريق حارس المرمى الدفاع
    SELECT Club_id INTO goalkeeper_club_id
    FROM Lineup
    WHERE Football_Match_id = match_id
      AND Player_id = NEW.Defending_Goalkeeper_Player_id;
    
    -- تحديد الفريق المتوقع لحارس المرمى بناءً على من يضرب الجزاء
    -- إذا ضرب ضارب من USMA (Club_id = 1) → حارس من الخصم
    -- إذا ضرب ضارب من الخصم → حارس من USMA (Club_id = 1)
    IF penalty_taker_club_id = 1 THEN
        -- ضرب USMA الجزاء → حارس من فريق الخصم
        SET expected_goalkeeper_club = match_opponent_club_id;
    ELSE
        -- ضرب الخصم الجزاء → حارس من USMA
        SET expected_goalkeeper_club = 1;
    END IF;
    
    -- التحقق من أن حارس المرمى من الفريق الصحيح
    IF goalkeeper_club_id != expected_goalkeeper_club THEN
        SET error_message = CONCAT(
            'خطأ: حارس المرمى #', NEW.Defending_Goalkeeper_Player_id,
            ' من الفريق #', goalkeeper_club_id,
            ' والفريق المتوقع هو #', expected_goalkeeper_club,
            ' (الذي يدافع ضد ضارب من الفريق #', penalty_taker_club_id, ')'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.7: الهداف وصانع الأسست يجب أن يكونا من نفس الفريق
--              والهداف في الملعب وليس مطروداً
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_validate_goal_scorer_assist_same_club
BEFORE INSERT ON Goal
FOR EACH ROW
BEGIN
    DECLARE assist_club INT;
    DECLARE scorer_club INT;
    DECLARE error_message VARCHAR(255);
    DECLARE match_id INT;
    DECLARE scorer_in_lineup INT;
    DECLARE assist_in_lineup INT;
    DECLARE is_scorer_red_carded INT;
    DECLARE event_minutes INT;
    
    IF NEW.Assist_Player_id IS NOT NULL THEN
        -- نفترض أن كلاهما من نفس الفريق (Club_id)
        -- هذا تحقق يدوي لأن الهداف والمساعد يجب أن يكونا من نفس الفريق الذي سجل الهدف
        IF NEW.Goalscorer_Player_id = NEW.Assist_Player_id THEN
            SET error_message = 'خطأ: لا يمكن لاعب أن يسجل ويصنع الهدف لنفسه';
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
        END IF;
    END IF;
    
    -- الحصول على معرف المباراة والدقيقة
    SELECT Football_Match_id, Event_Minutes INTO match_id, event_minutes
    FROM Event 
    WHERE Event_id = NEW.Event_id;
    
    -- التحقق من أن الهداف موجود في الملعب (Lineup)
    SELECT COUNT(*) INTO scorer_in_lineup
    FROM Lineup
    WHERE Football_Match_id = match_id
      AND Player_id = NEW.Goalscorer_Player_id
      AND Club_id = NEW.Club_id;
    
    IF scorer_in_lineup = 0 THEN
        SET error_message = CONCAT(
            'خطأ: الهداف #', NEW.Goalscorer_Player_id,
            ' لم يشارك مع الفريق #', NEW.Club_id
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
    
    -- التحقق من أن صانع الأسست موجود في الملعب (إذا كان موجود)
    IF NEW.Assist_Player_id IS NOT NULL THEN
        SELECT COUNT(*) INTO assist_in_lineup
        FROM Lineup
        WHERE Football_Match_id = match_id
          AND Player_id = NEW.Assist_Player_id
          AND Club_id = NEW.Club_id;
        
        IF assist_in_lineup = 0 THEN
            SET error_message = CONCAT(
                'خطأ: صانع الأسست #', NEW.Assist_Player_id,
                ' لم يشارك مع الفريق #', NEW.Club_id
            );
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
        END IF;
    END IF;
    
    -- التحقق من أن الهداف لم يكن مطروداً قبل التسجيل
    SELECT COUNT(*) INTO is_scorer_red_carded
    FROM Card
    JOIN Event ON Card.Event_id = Event.Event_id
    WHERE Event.Football_Match_id = match_id
      AND Card.Card_Type = 'Red'
      AND Card.Player_id = NEW.Goalscorer_Player_id
      AND Event.Event_Minutes < event_minutes;
    
    IF is_scorer_red_carded > 0 THEN
        SET error_message = CONCAT(
            'خطأ: الهداف #', NEW.Goalscorer_Player_id,
            ' كان مطروداً قبل التسجيل'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.8: التحقق من أن Penalty_Taker و Defending_Goalkeeper مختلفان
--              وأن ضارب الجزاء موجود في الملعب وليس مطروداً
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_validate_penalty_different_players
BEFORE INSERT ON Penalty
FOR EACH ROW
BEGIN
    DECLARE error_message VARCHAR(255);
    DECLARE match_id INT;
    DECLARE penalty_taker_count INT;
    DECLARE is_red_carded INT;
    DECLARE event_minutes INT;
    
    IF NEW.Penalty_Taker_Player_id = NEW.Defending_Goalkeeper_Player_id THEN
        SET error_message = 'خطأ: ضارب الجزاء وحارس المرمى يجب أن يكونا لاعبان مختلفان';
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
    
    -- الحصول على معرف المباراة
    SELECT Football_Match_id, Event_Minutes INTO match_id, event_minutes
    FROM Event 
    WHERE Event_id = NEW.Event_id;
    
    -- التحقق من أن ضارب الجزاء موجود في الملعب (Lineup)
    SELECT COUNT(*) INTO penalty_taker_count
    FROM Lineup
    WHERE Football_Match_id = match_id
      AND Player_id = NEW.Penalty_Taker_Player_id;
    
    IF penalty_taker_count = 0 THEN
        SET error_message = CONCAT(
            'خطأ: ضارب الجزاء #', NEW.Penalty_Taker_Player_id,
            ' لم يشارك في المباراة'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
    
    -- التحقق من أن ضارب الجزاء لم يكن مطروداً قبل ضربة الجزاء
    SELECT COUNT(*) INTO is_red_carded
    FROM Card
    JOIN Event ON Card.Event_id = Event.Event_id
    WHERE Event.Football_Match_id = match_id
      AND Card.Card_Type = 'Red'
      AND Card.Player_id = NEW.Penalty_Taker_Player_id
      AND Event.Event_Minutes < event_minutes;
    
    IF is_red_carded > 0 THEN
        SET error_message = CONCAT(
            'خطأ: ضارب الجزاء #', NEW.Penalty_Taker_Player_id,
            ' كان مطروداً قبل ضربة الجزاء'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.9: Is_Starter يجب أن يكون 1 فقط لـ Minute_In = 0
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_validate_starter_lineup
BEFORE INSERT ON Lineup
FOR EACH ROW
BEGIN
    DECLARE error_message VARCHAR(255);
    
    -- إذا كان اللاعب بديل (Is_Starter = 0) يجب أن يكون Minute_In > 0 أو NULL
    IF NEW.Is_Starter = 0 AND (NEW.Minute_In = 0 OR NEW.Minute_In IS NULL) THEN
        SET error_message = CONCAT(
            'خطأ: اللاعب #', NEW.Player_id, 
            ' مدرج كبديل لكن دقيقة الدخول = 0'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
    
    -- إذا كان اللاعب أساسي (Is_Starter = 1) يجب أن يكون Minute_In = 0
    IF NEW.Is_Starter = 1 AND NEW.Minute_In != 0 AND NEW.Minute_In IS NOT NULL THEN
        SET error_message = CONCAT(
            'خطأ: اللاعب #', NEW.Player_id, 
            ' مدرج كأساسي لكن دقيقة الدخول ≠ 0'
        );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = error_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- TRIGGER 2.10: التحقق من أن Game Status متسق مع الأحداث
-- ============================================================================
DELIMITER $$

CREATE TRIGGER trg_validate_match_status_consistent
BEFORE UPDATE ON Football_Match
FOR EACH ROW
BEGIN
    DECLARE event_count INT;
    
    -- إذا كانت المباراة مجدولة، يجب ألا تكون هناك أحداث
    IF NEW.Football_Match_Status = 'Scheduled' THEN
        SELECT COUNT(*) INTO event_count
        FROM Event
        WHERE Football_Match_id = NEW.Football_Match_id;
        
        IF event_count > 0 THEN
            SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'خطأ: مباراة مجدولة لا يمكن أن تحتوي على أحداث';
        END IF;
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER trg_validate_player_season_before_insert
BEFORE INSERT ON Player_Season
FOR EACH ROW
BEGIN
    DECLARE season_start DATE;
    DECLARE season_end DATE;
    DECLARE relationship_exists INT DEFAULT 0;

    SELECT
        STR_TO_DATE(CONCAT(Start_Year, '-07-01'), '%Y-%m-%d'),
        STR_TO_DATE(CONCAT(End_Year, '-06-30'), '%Y-%m-%d')
    INTO season_start, season_end
    FROM Season
    WHERE Season_Number = NEW.Season_Number;

    IF season_start IS NULL OR season_end IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
        'Player_Season: Season must have valid Start_Year and End_Year.';
    END IF;

    SELECT COUNT(*)
    INTO relationship_exists
    FROM Player_Club pc
    WHERE pc.Player_id = NEW.Player_id
      AND pc.Club_id = NEW.Club_id
      AND (pc.Join_Date IS NULL OR pc.Join_Date <= season_end)
      AND (pc.Leave_Date IS NULL OR pc.Leave_Date >= season_start);

    IF relationship_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
        'Player_Season: Player is not linked to this club during the selected season.';
    END IF;
END$$

DELIMITER ;


DELIMITER $$

CREATE TRIGGER trg_validate_player_season_before_update
BEFORE UPDATE ON Player_Season
FOR EACH ROW
BEGIN
    DECLARE season_start DATE;
    DECLARE season_end DATE;
    DECLARE relationship_exists INT DEFAULT 0;

    SELECT
        STR_TO_DATE(CONCAT(Start_Year, '-07-01'), '%Y-%m-%d'),
        STR_TO_DATE(CONCAT(End_Year, '-06-30'), '%Y-%m-%d')
    INTO season_start, season_end
    FROM Season
    WHERE Season_Number = NEW.Season_Number;

    IF season_start IS NULL OR season_end IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
        'Player_Season: Season must have valid Start_Year and End_Year.';
    END IF;

    SELECT COUNT(*)
    INTO relationship_exists
    FROM Player_Club pc
    WHERE pc.Player_id = NEW.Player_id
      AND pc.Club_id = NEW.Club_id
      AND (pc.Join_Date IS NULL OR pc.Join_Date <= season_end)
      AND (pc.Leave_Date IS NULL OR pc.Leave_Date >= season_start);

    IF relationship_exists = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
        'Player_Season: Player is not linked to this club during the selected season.';
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- ============ 3. VIEWS FOR DATA VALIDATION & REPORTING ==============
-- ============================================================================

-- View للتحقق من اللاعبين النشطين في كل مباراة
CREATE OR REPLACE VIEW v_active_players_in_match AS
SELECT 
    fm.Football_Match_id,
    fm.Football_Match_Date,
    l.Club_id,
    l.Player_id,
    p.Person_Display_Name,
    l.Is_Starter,
    l.Minute_In,
    l.Minute_Out,
    pc.Join_Date,
    pc.Leave_Date,
    DATEDIFF(fm.Football_Match_Date, pc.Join_Date) AS days_from_join,
    DATEDIFF(COALESCE(pc.Leave_Date, CURDATE()), fm.Football_Match_Date) AS days_until_leave
FROM Football_Match fm
JOIN Lineup l ON fm.Football_Match_id = l.Football_Match_id
JOIN Player p ON l.Player_id = p.Player_id
JOIN Person ps ON p.Person_id = ps.Person_id
JOIN Player_Club pc ON p.Player_id = pc.Player_id 
    AND l.Club_id = pc.Club_id
    AND pc.Is_Actual = 1;

-- View للتحقق من اللاعبين المطرودين وآخر أحداثهم
CREATE OR REPLACE VIEW v_red_cards_and_events AS
SELECT 
    c.Card_id,
    e_card.Football_Match_id,
    e_card.Event_Minutes,
    c.Player_id,
    p.Person_Display_Name,
    'Red Card' AS event_type_red,
    COUNT(e_after.Event_id) AS events_after_red_card
FROM Card c
JOIN Event e_card ON c.Event_id = e_card.Event_id
JOIN Player pl ON c.Player_id = pl.Player_id
JOIN Person p ON pl.Person_id = p.Person_id
LEFT JOIN Event e_after ON e_card.Football_Match_id = e_after.Football_Match_id
    AND e_after.Event_Minutes > e_card.Event_Minutes
    AND c.Player_id = (
        CASE 
            WHEN e_after.Event_Type = 'Goal' THEN (SELECT Goalscorer_Player_id FROM Goal WHERE Event_id = e_after.Event_id)
            WHEN e_after.Event_Type = 'Substitution' THEN (SELECT Player_In_id FROM Substitution WHERE Event_id = e_after.Event_id)
            ELSE NULL
        END
    )
WHERE c.Card_Type = 'Red'
GROUP BY c.Card_id;

-- View للتحقق من الأخطاء المحتملة في البيانات
CREATE OR REPLACE VIEW v_data_validation_errors AS
SELECT 
    'Opponent = USMA' AS error_type,
    Football_Match_id,
    NULL AS player_id,
    NULL AS details
FROM Football_Match
WHERE Opponent_Club_id = 1

UNION ALL

SELECT 
    'Player Outside Contract Period' AS error_type,
    l.Football_Match_id,
    l.Player_id,
    CONCAT('Match: ', fm.Football_Match_Date, ', Contract: ', 
           pc.Join_Date, ' to ', COALESCE(pc.Leave_Date, 'Active'))
FROM Lineup l
JOIN Football_Match fm ON l.Football_Match_id = fm.Football_Match_id
JOIN Player_Club pc ON l.Player_id = pc.Player_id AND l.Club_id = pc.Club_id
WHERE fm.Football_Match_Date < pc.Join_Date 
   OR (pc.Leave_Date IS NOT NULL AND fm.Football_Match_Date > pc.Leave_Date)

UNION ALL

SELECT 
    'Same Player In and Out in Sub' AS error_type,
    e.Football_Match_id,
    s.Player_In_id,
    CONCAT('Player_Out: ', s.Player_Out_id, ', Player_In: ', s.Player_In_id)
FROM Substitution s
JOIN Event e ON s.Event_id = e.Event_id
WHERE s.Player_In_id = s.Player_Out_id;

-- ============================================================================
-- ============ 4. UTILITY PROCEDURES ==============
-- ============================================================================

-- Procedure للتحقق من سلامة بيانات مباراة معينة
DELIMITER $$

CREATE PROCEDURE sp_validate_match(IN match_id INT)
BEGIN
    DECLARE error_count INT;
    
    SELECT COUNT(*) INTO error_count
    FROM v_data_validation_errors
    WHERE error_type IN (
        'Opponent = USMA',
        'Player Outside Contract Period'
    )
    AND Football_Match_id = match_id;
    
    IF error_count > 0 THEN
        SELECT CONCAT('⚠️ وجدت ', error_count, ' أخطاء في البيانات:') AS validation_message;
        SELECT * FROM v_data_validation_errors 
        WHERE Football_Match_id = match_id;
    ELSE
        SELECT '✓ المباراة سليمة من حيث البيانات' AS validation_message;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- ملاحظات مهمة:
-- ============================================================================
/*
1. CHECK Constraints: سريعة وفعالة للتحقق من الشروط البسيطة
2. Triggers: تُستخدم للمنطق المعقد الذي يتطلب فحوصات بين الجداول
3. Views: توفر طريقة سهلة للتحقق من البيانات والتقارير
4. Procedures: توفر واجهات موثقة للعمليات الدقيقة

الأخطاء سيتم طرحها عند الإدراج، لذا تأكد من التعامل معها في التطبيق!
*/



INSERT INTO `Continent` VALUES (1, 'Africa',        'افريقيا');
INSERT INTO `Continent` VALUES (2, 'Asia',          'آسيا');
INSERT INTO `Continent` VALUES (3, 'Europe',        'أوروبا');
INSERT INTO `Continent` VALUES (4, 'North America', 'أمريكا الشمالية');
INSERT INTO `Continent` VALUES (5, 'South America', 'أمريكا الجنوبية');
INSERT INTO `Continent` VALUES (6, 'Oceania',       'أوقيانوسيا');



INSERT INTO `Country` VALUES(1  ,'AF','Afghanistan'                                     ,'أفغانستان'                                         ,  'AFG'     ,  93      , 2);
INSERT INTO `Country` VALUES(2  ,'AL','Albania'                                         , 'ألبانيا'                                          ,  'ALB'     ,  355     , 3);
INSERT INTO `Country` VALUES(3  ,'DZ','Algeria'                                         , 'الجزائر'                                          ,  'DZA'     ,  213     , 1);
INSERT INTO `Country` VALUES(4  ,'AS','American Samoa'                                  , 'ساموا-الأمريكي'                                   ,  'ASM'     ,  1684    , 6);
INSERT INTO `Country` VALUES(5  ,'AD','Andorra'                                         , 'أندورا'                                           ,  'AND'     ,  376     , 3);
INSERT INTO `Country` VALUES(6  ,'AO','Angola'                                          , 'أنغولا'                                            ,  'AGO'     ,  244     , 1);
INSERT INTO `Country` VALUES(7  ,'AI','Anguilla'                                        , 'أنغويلا'                                           ,  'AIA'     ,  1264    , 4);
INSERT INTO `Country` VALUES(8  ,'AG','Antigua and Barbuda'                             , 'أنتيغوا وبربودا'                                 ,  'ATG'     ,  1268    , 4);
INSERT INTO `Country` VALUES(9  ,'AR','Argentina'                                       , 'الأرجنتين'                                         ,  'ARG'     ,  54      , 5);
INSERT INTO `Country` VALUES(10 ,'AM','Armenia'                                         , 'أرمينيا'                                         ,  'ARM'     ,  374     , 3);
INSERT INTO `Country` VALUES(11 ,'AW','Aruba'                                           , 'أروبه'                                            ,  'ABW'     ,  297     , 4);
INSERT INTO `Country` VALUES(12 ,'AU','Australia'                                       , 'أستراليا'                                         ,  'AUS'     ,  61      , 2);
INSERT INTO `Country` VALUES(13 ,'AT','Austria'                                         , 'النمسا'                                           ,  'AUT'     ,  43      , 3);
INSERT INTO `Country` VALUES(14 ,'AZ','Azerbaijan'                                      , 'أذربيجان'                                         ,  'AZE'     ,  994     , 3);
INSERT INTO `Country` VALUES(15 ,'BS','Bahamas'                                         , 'الباهاماس'                                        ,  'BHS'     ,  1242    , 4);
INSERT INTO `Country` VALUES(16 ,'BH','Bahrain'                                         , 'البحرين'                                          ,  'BHR'     ,  973     , 2);
INSERT INTO `Country` VALUES(17 ,'BD','Bangladesh'                                      , 'بنغلاديش'                                          ,  'BGD'     ,  880     , 2);
INSERT INTO `Country` VALUES(18 ,'BB','Barbados'                                        , 'بربادوس'                                          ,  'BRB'     ,  246     , 4);
INSERT INTO `Country` VALUES(19 ,'BY','Belarus'                                         , 'روسيا البيضاء'                                    ,  'BLR'     ,  375     , 3);
INSERT INTO `Country` VALUES(20 ,'BE','Belgium'                                         , 'بلجيكا'                                           ,  'BEL'     ,  32      , 3);
INSERT INTO `Country` VALUES(21 ,'BZ','Belize'                                          , 'بيليز'                                            ,  'BLZ'     ,  501     , 4);
INSERT INTO `Country` VALUES(22 ,'BJ','Benin'                                           , 'بنين'                                             ,  'BEN'     ,  229     , 1);
INSERT INTO `Country` VALUES(23 ,'BM','Bermuda'                                         , 'جزر برمودا'                                       ,  'BMU'     ,  1441    , 4);
INSERT INTO `Country` VALUES(24 ,'BT','Bhutan'                                          , 'بوتان'                                            ,  'BTN'     ,  975     , 2);
INSERT INTO `Country` VALUES(25 ,'BO','Bolivia'                                         , 'بوليفيا'                                          ,  'BOL'     ,  591     , 5);
INSERT INTO `Country` VALUES(26 ,'BQ','Bonaire'                                         , 'بونير'                                            ,  'BES'     ,  599     , 4);
INSERT INTO `Country` VALUES(27 ,'BA','Bosnia and Herzegovina'                          , 'البوسنة و الهرسك'                                 ,  'BIH'     ,  387    , 3);
INSERT INTO `Country` VALUES(28 ,'BW','Botswana'                                        , 'بوتسوانا'                                         ,  'BWA'     ,  267     , 1);
INSERT INTO `Country` VALUES(29 ,'BR','Brazil'                                          , 'البرازيل'                                         ,  'BRA'     ,  55      , 5);
INSERT INTO `Country` VALUES(30 ,'VG','British Virgin Islands'                          ,'جزر فيرجن البريطانية'                             ,  'VGB'     ,  1284    , 4);
INSERT INTO `Country` VALUES(31 ,'BN','Brunei Darussalam'                               , 'بروني'                                            ,  'BRN'     ,  673     , 2);
INSERT INTO `Country` VALUES(32 ,'BG','Bulgaria'                                        , 'بلغاريا'                                          ,  'BGR'     ,  359     , 3);
INSERT INTO `Country` VALUES(33 ,'BF','Burkina Faso'                                    , 'بوركينا فاسو'                                     ,  'BFA'     ,  226     , 1);
INSERT INTO `Country` VALUES(34 ,'BI','Burundi'                                         , 'بوروندي'                                          ,  'BDI'     ,  257     , 1);
INSERT INTO `Country` VALUES(35 ,'KH','Cambodia'                                        , 'كمبوديا'                                          ,  'KHM'     ,  855     , 2);
INSERT INTO `Country` VALUES(36 ,'CM','Cameroon'                                        , 'كاميرون'                                          ,  'CMR'     ,  237     , 1);
INSERT INTO `Country` VALUES(37 ,'CA','Canada'                                          , 'كندا'                                             ,  'CAN'     ,  1        , 4);
INSERT INTO `Country` VALUES(38 ,'CV','Cape Verde'                                      , 'الرأس الأخضر'                                      ,  'CPV'     ,  238     , 1);
INSERT INTO `Country` VALUES(39 ,'KY','Cayman Islands'                                  , 'جزر كايمان'                                       ,  'CYM'     ,  1345    , 4);
INSERT INTO `Country` VALUES(40 ,'CF','Central African Republic'                        , 'جمهورية أفريقيا الوسطى'                          ,  'CAF'     ,  236     , 1);
INSERT INTO `Country` VALUES(41 ,'TD','Chad'                                            , 'تشاد'                                             ,  'TCD'     ,  235      , 1);
INSERT INTO `Country` VALUES(42 ,'CL','Chile'                                           , 'شيلي'                                             ,  'CHL'     ,  56       , 5);
INSERT INTO `Country` VALUES(43 ,'CN','China'                                           , 'الصين'                                            ,  'CHN'     ,  86       , 2);
INSERT INTO `Country` VALUES(44 ,'CO','Colombia'                                        , 'كولومبيا'                                         ,  'COL'     ,  57      , 5);
INSERT INTO `Country` VALUES(45 ,'KM','Comoros'                                         , 'جزر القمر'                                        ,  'COM'     ,  269     , 1);
INSERT INTO `Country` VALUES(46 ,'CG','Congo'                                           , 'الكونغو'                                          ,  'COG'     ,  242     , 1);
INSERT INTO `Country` VALUES(47 ,'CK','Cook Islands'                                    , 'جزر كوك'                                          ,  'COK'     ,  682     , 6);
INSERT INTO `Country` VALUES(48 ,'CR','Costa Rica'                                      , 'كوستاريكا'                                        ,  'CRI'     ,  506     , 4);
INSERT INTO `Country` VALUES(49 ,'HR','Croatia'                                         , 'كرواتيا'                                          ,  'HRV'     ,  385     , 3);
INSERT INTO `Country` VALUES(50 ,'CU','Cuba'                                            , 'كوبا'                                             ,  'CUB'     ,  53      , 4);
INSERT INTO `Country` VALUES(51 ,'CW','Curaçao'                                         , 'كوراساو'                                          ,  'CUW'     ,  599     , 4);
INSERT INTO `Country` VALUES(52 ,'CY','Cyprus'                                          , 'قبرص'                                             ,  'CYP'     ,  357     , 3);
INSERT INTO `Country` VALUES(53 ,'CZ','Czech Republic'                                  , 'الجمهورية التشيكية'                              ,  'CZE'     ,  420    , 3);
INSERT INTO `Country` VALUES(54 ,'DK','Denmark'                                         , 'الدانمارك'                                        ,  'DNK'     ,  45      , 3);
INSERT INTO `Country` VALUES(55 ,'DJ','Djibouti'                                        , 'جيبوتي'                                           ,  'DJI'     ,  253     , 1);
INSERT INTO `Country` VALUES(56 ,'DM','Dominica'                                        , 'دومينيكا'                                         ,  'DMA'     ,  1767    , 4);
INSERT INTO `Country` VALUES(57 ,'DO','Dominican Republic'                              , 'الجمهورية الدومينيكية'                           ,  'DOM'     ,  1809   , 4);
INSERT INTO `Country` VALUES(58 ,'CD','Democratic Republic of the Congo'                , 'جمهورية الكونغو الديمقراطية'                    ,  'COD'     ,  243     , 1);
INSERT INTO `Country` VALUES(59 ,'EC','Ecuador'                                         , 'إكوادور'                                          ,  'ECU'     ,  593     , 5);
INSERT INTO `Country` VALUES(60 ,'EG','Egypt'                                           , 'مصر'                                              ,  'EGY'     ,  20      , 1);
INSERT INTO `Country` VALUES(61 ,'SV','El Salvador'                                     , 'إلسلفادور'                                        ,  'SLV'     ,  503     , 4);
INSERT INTO `Country` VALUES(62 ,'EN','England'                                         , 'إنجلترا'                                          ,  'ENG'     ,  44      , 3);
INSERT INTO `Country` VALUES(63 ,'GQ','Equatorial Guinea'                               , 'غينيا الاستوائية'                                 ,  'GNQ'     ,  240     , 1);
INSERT INTO `Country` VALUES(64 ,'ER','Eritrea'                                         , 'إريتريا'                                          ,  'ERI'     ,  291     , 1);
INSERT INTO `Country` VALUES(65 ,'EE','Estonia'                                         , 'استونيا'                                          ,  'EST'     ,  372     , 3);
INSERT INTO `Country` VALUES(66 ,'SZ','Eswatini'                                        , 'اسواتيني'                                         ,  'SWZ'     ,  268     , 1);
INSERT INTO `Country` VALUES(67 ,'ET','Ethiopia'                                        , 'أثيوبيا'                                          ,  'ETH'     ,  251     , 1);
INSERT INTO `Country` VALUES(68 ,'FO','Faroe Islands'                                   , 'جزر فارو'                                         ,  'FRO'     ,  298     , 3);
INSERT INTO `Country` VALUES(69 ,'FJ','Fiji'                                            , 'فيجي'                                             ,  'FJI'     ,  679     , 6);
INSERT INTO `Country` VALUES(70 ,'FI','Finland'                                         , 'فنلندا'                                           ,  'FIN'     ,  358     , 3);
INSERT INTO `Country` VALUES(71 ,'FR','France'                                          , 'فرنسا'                                            ,  'FRA'     ,  33      , 3);
INSERT INTO `Country` VALUES(72 ,'GF','French Guiana'                                   , 'غويانا الفرنسية'                                 ,  'GUF'     ,  594     , 4);
INSERT INTO `Country` VALUES(73 ,'GA','Gabon'                                           , 'الغابون'                                          ,  'GAB'     ,  241     , 1);
INSERT INTO `Country` VALUES(74 ,'GM','Gambia'                                          , 'غامبيا'                                           ,  'GMB'     ,  220     , 1);
INSERT INTO `Country` VALUES(75 ,'GE','Georgia'                                         , 'جيورجيا'                                          ,  'GEO'     ,  995     , 3);
INSERT INTO `Country` VALUES(76 ,'DE','Germany'                                         , 'ألمانيا'                                          ,  'DEU'     ,  49      , 3);
INSERT INTO `Country` VALUES(77 ,'GH','Ghana'                                           , 'غانا'                                             ,  'GHA'     ,  233     , 1);
INSERT INTO `Country` VALUES(78 ,'GI','Gibraltar'                                       , 'جبل طارق'                                         ,  'GIB'     ,  350     , 3);
INSERT INTO `Country` VALUES(79 ,'GR','Greece'                                          , 'اليونان'                                          ,  'GRC'     ,  30      , 3);
INSERT INTO `Country` VALUES(80 ,'GD','Grenada'                                         , 'غرينادا'                                          ,  'GRD'     ,  1473    , 4);
INSERT INTO `Country` VALUES(81 ,'GP','Guadeloupe'                                      , 'جزر جوادلوب'                                      ,  'GLP'     ,  590     , 4);
INSERT INTO `Country` VALUES(82 ,'GU','Guam'                                            , 'جوام'                                             ,  'GUM'     ,  1671    , 2);
INSERT INTO `Country` VALUES(83 ,'GT','Guatemala'                                       , 'غواتيمال'                                         ,  'GTM'     ,  502     , 4);
INSERT INTO `Country` VALUES(84 ,'GN','Guinea'                                          , 'غينيا'                                            ,  'GIN'     ,  224     , 1);
INSERT INTO `Country` VALUES(85 ,'GW','Guinea-Bissau'                                   , 'غينيا-بيساو'                                      ,  'GNB'     ,  245     , 1);
INSERT INTO `Country` VALUES(86 ,'GY','Guyana'                                          , 'غيانا'                                            ,  'GUY'     ,  592     , 4);
INSERT INTO `Country` VALUES(87 ,'HT','Haiti'                                           , 'هايتي'                                            ,  'HTI'     ,  509     , 4);
INSERT INTO `Country` VALUES(88 ,'HN','Honduras'                                        , 'هندوراس'                                          ,  'HND'     ,  504     , 4);
INSERT INTO `Country` VALUES(89 ,'HK','Hong Kong'                                       , 'هونغ كونغ'                                        ,  'HKG'     ,  852     , 2);
INSERT INTO `Country` VALUES(90 ,'HU','Hungary'                                         , 'المجر'                                            ,  'HUN'     ,  36      , 3);
INSERT INTO `Country` VALUES(91 ,'IS','Iceland'                                         , 'آيسلندا'                                          ,  'ISL'     ,  354     , 3);
INSERT INTO `Country` VALUES(92 ,'IN','India'                                           , 'الهند'                                            ,  'IND'     ,  91      , 2);
INSERT INTO `Country` VALUES(93 ,'ID','Indonesia'                                       , 'أندونيسيا'                                        ,  'IDN'     ,  62      , 2);
INSERT INTO `Country` VALUES(94 ,'IR','Iran'                                            , 'إيران'                                            ,  'IRN'     ,  98      , 2);
INSERT INTO `Country` VALUES(95 ,'IQ','Iraq'                                            , 'العراق'                                           ,  'IRQ'     ,  964     , 2);
INSERT INTO `Country` VALUES(96 ,'IE','Ireland'                                         , 'إيرلندا'                                          ,  'IRL'     ,  353     , 3);
INSERT INTO `Country` VALUES(97 ,'IT','Italy'                                           , 'إيطاليا'                                          ,  'ITA'     ,  39      , 3);
INSERT INTO `Country` VALUES(98 ,'CI','Ivory Coast'                                     , 'ساحل العاج'                                       ,  'CIV'     ,  225     , 1);
INSERT INTO `Country` VALUES(99 ,'JM','Jamaica'                                         , 'جمايكا'                                           ,  'JAM'     ,  1876    , 4);
INSERT INTO `Country` VALUES(100,'JP','Japan'                                           , 'اليابان'                                          ,  'JPN'     ,  81      , 2);
INSERT INTO `Country` VALUES(101,'JO','Jordan'                                          , 'الأردن'                                            ,  'JOR'     ,  962     , 2);
INSERT INTO `Country` VALUES(102,'KZ','Kazakhstan'                                      , 'كازاخستان'                                        ,  'KAZ'     ,  7       , 3);
INSERT INTO `Country` VALUES(103,'KE','Kenya'                                           , 'كينيا'                                            ,  'KEN'     ,  254     , 1);
INSERT INTO `Country` VALUES(104,'KI','Kiribati'                                        , 'كيريباتي'                                         ,  'KIR'     ,  686     , 6);
INSERT INTO `Country` VALUES(105,'KP','Korea(North Korea)'                              , 'كوريا الشمالية'                                   ,  'PRK'     ,  850     , 2);
INSERT INTO `Country` VALUES(106,'KR','Korea(South Korea)'                              , 'كوريا الجنوبية'                                   ,  'KOR'     ,  82      , 2);
INSERT INTO `Country` VALUES(107,'XK','Kosovo'                                          , 'كوسوفو'                                           ,   'XKX'     ,  383    , 3);
INSERT INTO `Country` VALUES(108,'KW','Kuwait'                                          , 'الكويت'                                           ,  'KWT'     ,  965     , 2);
INSERT INTO `Country` VALUES(109,'KG','Kyrgyzstan'                                      , 'قيرغيزستان'                                       ,  'KGZ'     ,  996     , 2);
INSERT INTO `Country` VALUES(110,'LA','Lao PDR'                                         , 'لاوس'                                              ,  'LAO'     ,  856      , 2);
INSERT INTO `Country` VALUES(111,'LV','Latvia'                                          , 'لاتفيا'                                            ,  'LVA'     ,  371      , 3);
INSERT INTO `Country` VALUES(112,'LB','Lebanon'                                         , 'لبنان'                                            ,  'LBN'     ,  961      , 2);
INSERT INTO `Country` VALUES(113,'LS','Lesotho'                                         , 'ليسوتو'                                           ,  'LSO'     ,  266      , 1);
INSERT INTO `Country` VALUES(114,'LR','Liberia'                                         , 'ليبيريا'                                          ,  'LBR'     ,  231      , 1);
INSERT INTO `Country` VALUES(115,'LY','Libya'                                           , 'ليبيا'                                            ,  'LBY'     ,  218      , 1);
INSERT INTO `Country` VALUES(116,'LI','Liechtenstein'                                   , 'ليختنشتين'                                        ,  'LIE'     ,  423     , 3);
INSERT INTO `Country` VALUES(117,'LT','Lithuania'                                       , 'لتوانيا'                                          ,  'LTU'     ,  370      , 3);
INSERT INTO `Country` VALUES(118,'LU','Luxembourg'                                      , 'لوكسمبورغ'                                        ,  'LUX'     ,  352     , 3);
INSERT INTO `Country` VALUES(119,'MO','Macau'                                           , 'ماكاو'                                            ,  'MAC'     ,  853     , 2);
INSERT INTO `Country` VALUES(120,'MG','Madagascar'                                      , 'مدغشقر'                                           ,  'MDG'     ,  261     , 1);
INSERT INTO `Country` VALUES(121,'MW','Malawi'                                          , 'مالاوي'                                            ,  'MWI'     ,  265     , 1);
INSERT INTO `Country` VALUES(122,'MY','Malaysia'                                        , 'ماليزيا'                                          ,  'MYS'     ,  60      , 2);
INSERT INTO `Country` VALUES(123,'MV','Maldives'                                        , 'المالديف'                                         ,  'MDV'     ,  960     , 2);
INSERT INTO `Country` VALUES(124,'ML','Mali'                                            , 'مالي'                                             ,  'MLI'     ,  223     , 1);
INSERT INTO `Country` VALUES(125,'MT','Malta'                                           , 'مالطا'                                            ,  'MLT'     ,  356     , 3);
INSERT INTO `Country` VALUES(126,'MQ','Martinique'                                      , 'مارتينيك'                                         ,  'MTQ'     ,  596     , 4);
INSERT INTO `Country` VALUES(127,'MR','Mauritania'                                      , 'موريتانيا'                                        ,  'MRT'     ,  222     , 1);
INSERT INTO `Country` VALUES(128,'MU','Mauritius'                                       , 'موريشيوس'                                         ,  'MUS'     ,  230     , 1);
INSERT INTO `Country` VALUES(129,'MX','Mexico'                                          , 'المكسيك'                                          ,  'MEX'     ,  52      , 4);
INSERT INTO `Country` VALUES(130,'MD','Moldova'                                         , 'مولدوفيا'                                         ,  'MDA'     ,  373     , 3);
INSERT INTO `Country` VALUES(131,'MN','Mongolia'                                        , 'منغوليا'                                          ,  'MNG'     ,  976     , 2);
INSERT INTO `Country` VALUES(132,'MS','Montserrat'                                      , 'مونتسيرات'                                        ,  'MSR'     ,  1664    , 4);
INSERT INTO `Country` VALUES(133,'ME','Montenegro'                                      , 'الجبل الأسود'                                      ,  'MNE'     ,  382     , 3);
INSERT INTO `Country` VALUES(134,'MA','Morocco'                                         , 'المغرب'                                           ,  'MAR'     ,  212     , 1);
INSERT INTO `Country` VALUES(135,'MZ','Mozambique'                                      , 'موزمبيق'                                          ,  'MOZ'     ,  258     , 1);
INSERT INTO `Country` VALUES(136,'MM','Myanmar'                                         , 'ميانمار'                                          ,  'MMR'     ,  95      , 2);
INSERT INTO `Country` VALUES(137,'NA','Namibia'                                         , 'ناميبيا'                                          ,  'NAM'     ,  264     , 1);
INSERT INTO `Country` VALUES(138,'NP','Nepal'                                           , 'نيبال'                                            ,  'NPL'     ,  977     , 2);
INSERT INTO `Country` VALUES(139,'NL','Netherlands'                                     , 'هولندا'                                           ,  'NLD'     ,  31      , 3);
INSERT INTO `Country` VALUES(140,'NC','New Caledonia'                                   , 'كاليدونيا الجديدة'                               ,  'NCL'     ,  687     , 6);
INSERT INTO `Country` VALUES(141,'NZ','New Zealand'                                     , 'نيوزيلندا'                                        ,  'NZL'     ,  64      , 6);
INSERT INTO `Country` VALUES(142,'NI','Nicaragua'                                       , 'نيكاراجوا'                                        ,  'NIC'     ,  505     , 4);
INSERT INTO `Country` VALUES(143,'NE','Niger'                                           , 'النيجر'                                           ,  'NER'     ,  227     , 1);
INSERT INTO `Country` VALUES(144,'NG','Nigeria'                                         , 'نيجيريا'                                          ,  'NGA'     ,  234     , 1);
INSERT INTO `Country` VALUES(145,'XN','Northern Ireland'                                , 'أيرلندا الشمالية'                                ,  'NIR'     ,  44      , 3);
INSERT INTO `Country` VALUES(146,'MP','Northern Mariana Islands'                        , 'جزر ماريانا الشمالية'                            ,  'MNP'     ,  1670    , 2);
INSERT INTO `Country` VALUES(147,'MK','North Macedonia'                                 , 'مقدونيا الشمالية'                                ,  'MKD'     ,  389     , 3);
INSERT INTO `Country` VALUES(148,'NO','Norway'                                          , 'النرويج'                                          ,  'NOR'     ,  47      , 3);
INSERT INTO `Country` VALUES(149,'OM','Oman'                                            , 'عمان'                                             ,  'OMN'     ,  968     , 2);
INSERT INTO `Country` VALUES(150,'PK','Pakistan'                                        , 'باكستان'                                          ,  'PAK'     ,  92      , 2);
INSERT INTO `Country` VALUES(151,'PS','Palestine'                                       , 'فلسطين'                                           ,  'PLE'     ,  970     , 2);
INSERT INTO `Country` VALUES(152,'PA','Panama'                                          , 'بنما'                                             ,  'PAN'     ,  507     , 4);
INSERT INTO `Country` VALUES(153,'PG','Papua New Guinea'                                , 'بابوا غينيا الجديدة'                             ,  'PNG'     ,  675     , 6);
INSERT INTO `Country` VALUES(154,'PY','Paraguay'                                        , 'باراغواي'                                         ,  'PRY'     ,  595     , 5);
INSERT INTO `Country` VALUES(155,'PE','Peru'                                            , 'بيرو'                                             ,  'PER'     ,  51      , 5);
INSERT INTO `Country` VALUES(156,'PH','Philippines'                                     , 'الفليبين'                                         ,  'PHL'     ,  63      , 2);
INSERT INTO `Country` VALUES(157,'PL','Poland'                                          , 'بولونيا'                                          ,  'POL'     ,  48      , 3);
INSERT INTO `Country` VALUES(158,'PT','Portugal'                                        , 'البرتغال'                                         ,  'PRT'     ,  351     , 3);
INSERT INTO `Country` VALUES(159,'PR','Puerto Rico'                                     , 'بورتو ريكو'                                       ,  'PRI'     ,  1787    , 4);
INSERT INTO `Country` VALUES(160,'QA','Qatar'                                           , 'قطر'                                              ,  'QAT'     ,  974     , 2);
INSERT INTO `Country` VALUES(161,'RE','Reunion Island'                                  , 'ريونيون'                                          ,  'REU'     ,  262     , 1);
INSERT INTO `Country` VALUES(162,'RO','Romania'                                         , 'رومانيا'                                          ,  'ROM'     ,  40      , 3);
INSERT INTO `Country` VALUES(163,'RU','Russia'                                          , 'روسيا'                                            ,  'RUS'     ,  70      , 3);
INSERT INTO `Country` VALUES(164,'RW','Rwanda'                                          , 'رواندا'                                           ,  'RWA'     ,  250     , 1);
INSERT INTO `Country` VALUES(165,'KN','Saint Kitts and Nevis'                           , 'سانت كيتس ونيفس'                                 ,  'KNA'     ,  1869    , 4);
INSERT INTO `Country` VALUES(166,'LC','Saint Lucia'                                     , 'سانت لوسيا'                                       ,  'LCA'     ,  1758    , 4);
INSERT INTO `Country` VALUES(167,'MF','Saint Martin'                                    , 'سانت مارتن'                                       ,  'MAF'     ,  590     , 4);
INSERT INTO `Country` VALUES(168,'VC','Saint Vincent and the Grenadines'                , 'سانت فنسنت وجزر غرينادين'                        ,  'VCT'     ,  1784    , 4);
INSERT INTO `Country` VALUES(169,'SX','Sint Maarten'                                    , 'سينت مارتن'                                       ,  'SXM'     ,  1721    , 4);
INSERT INTO `Country` VALUES(170,'WS','Samoa'                                           , 'ساموا'                                            ,  'WSM'     ,  684     , 6);
INSERT INTO `Country` VALUES(171,'SM','San Marino'                                      , 'سان مارينو'                                       ,  'SMR'     ,  378     , 3);
INSERT INTO `Country` VALUES(172,'ST','Sao Tome and Principe'                           , 'ساو تومي وبرينسيبي'                              ,  'STP'     ,  239     , 1);
INSERT INTO `Country` VALUES(173,'SA','Saudi Arabia'                                    , 'المملكة العربية السعودية'                        ,  'SAU'     ,  966     , 2);
INSERT INTO `Country` VALUES(174,'XS','Scotland'                                        , 'اسكتلندا'                                         ,  'SCT'     ,  44      , 3);
INSERT INTO `Country` VALUES(175,'SN','Senegal'                                         , 'السنغال'                                          ,  'SEN'     ,  221     , 1);
INSERT INTO `Country` VALUES(176,'RS','Serbia'                                          , 'صربيا'                                            ,  'SRB'     ,  381     , 3);
INSERT INTO `Country` VALUES(177,'SC','Seychelles'                                      , 'سيشيل'                                            ,  'SYC'     ,  248     , 1);
INSERT INTO `Country` VALUES(178,'SL','Sierra Leone'                                    , 'سيراليون'                                         ,  'SLE'     ,  232     , 1);
INSERT INTO `Country` VALUES(179,'SG','Singapore'                                       , 'سنغافورة'                                         ,  'SGP'     ,  65      , 2);
INSERT INTO `Country` VALUES(180,'SK','Slovakia'                                        , 'سلوفاكيا'                                         ,  'SVK'     ,  421     , 3);
INSERT INTO `Country` VALUES(181,'SI','Slovenia'                                        , 'سلوفينيا'                                         ,  'SVN'     ,  386     , 3);
INSERT INTO `Country` VALUES(182,'SB','Solomon Islands'                                 , 'جزر سليمان'                                       ,  'SLB'     ,  677     , 6);
INSERT INTO `Country` VALUES(183,'SO','Somalia'                                         , 'الصومال'                                          ,  'SOM'     ,  252     , 1);
INSERT INTO `Country` VALUES(184,'ZA','South Africa'                                    , 'جنوب أفريقيا'                                     ,  'ZAF'     ,  27      , 1);
INSERT INTO `Country` VALUES(185,'SS','South Sudan'                                     , 'جنوب السودان'                                     ,  'SSD'     ,  211     , 1);
INSERT INTO `Country` VALUES(186,'ES','Spain'                                           , 'إسبانيا'                                          ,  'ESP'     ,  34      , 3);
INSERT INTO `Country` VALUES(187,'LK','Sri Lanka'                                       , 'سريلانكا'                                          ,  'LKA'     ,  94      , 2);
INSERT INTO `Country` VALUES(188,'SD','Sudan'                                           , 'السودان'                                          ,  'SDN'     ,  249     , 1);
INSERT INTO `Country` VALUES(189,'SR','Suriname'                                        , 'سورينام'                                          ,  'SUR'     ,  597     , 4);
INSERT INTO `Country` VALUES(190,'SE','Sweden'                                          , 'السويد'                                           ,  'SWE'     ,  46      , 3);
INSERT INTO `Country` VALUES(191,'CH','Switzerland'                                     , 'سويسرا'                                           ,  'CHE'     ,  41      , 3);
INSERT INTO `Country` VALUES(192,'SY','Syria'                                           , 'سوريا'                                            ,  'SYR'     ,  963     , 2);
INSERT INTO `Country` VALUES(193,'PF','Tahiti'                                          , 'تاهيتي'                                           ,  'TAH'     ,  689     , 6);
INSERT INTO `Country` VALUES(194,'TW','Taiwan (Chinese Taipei)'                         , 'تايوان (تايبيه الصينية)'                         ,  'TWN'     ,  886     , 2);
INSERT INTO `Country` VALUES(195,'TJ','Tajikistan'                                      , 'طاجيكستان'                                        ,  'TJK'     ,  992     , 2);
INSERT INTO `Country` VALUES(196,'TZ','Tanzania'                                        , 'تنزانيا'                                          ,  'TZA'     ,  255     , 1);
INSERT INTO `Country` VALUES(197,'TH','Thailand'                                        , 'تايلندا'                                          ,  'THA'     ,  66      , 2);
INSERT INTO `Country` VALUES(198,'TL','Timor-Leste'                                     , 'تيمور الشرقية'                                    ,  'TLS'     ,  670     , 2);
INSERT INTO `Country` VALUES(199,'TG','Togo'                                            , 'توغو'                                              ,  'TGO'     ,  228     , 1);
INSERT INTO `Country` VALUES(200,'TO','Tonga'                                           , 'تونغا'                                             ,  'TON'     ,  676     , 6);
INSERT INTO `Country` VALUES(201,'TT','Trinidad and Tobago'                             , 'ترينيداد وتوباغو'                                 ,  'TTO'     ,  1868    , 4);
INSERT INTO `Country` VALUES(202,'TN','Tunisia'                                         , 'تونس'                                              ,  'TUN'     ,  216     , 1);
INSERT INTO `Country` VALUES(203,'TR','Turkey'                                          , 'تركيا'                                             ,  'TUR'     ,  90      , 3);
INSERT INTO `Country` VALUES(204,'TM','Turkmenistan'                                    , 'تركمانستان'                                        ,  'TKM'     ,  7370   , 2);
INSERT INTO `Country` VALUES(205,'TC','Turks and Caicos Islands'                        , 'جزر توركس وكايكوس'                                ,  'TCA'     ,  1649    , 4);
INSERT INTO `Country` VALUES(206,'TV','Tuvalu'                                          , 'توفالو'                                            ,  'TUV'     ,  688     , 6);
INSERT INTO `Country` VALUES(207,'UG','Uganda'                                          , 'أوغندا'                                            ,  'UGA'     ,  256     , 1);
INSERT INTO `Country` VALUES(208,'UA','Ukraine'                                         , 'أوكرانيا'                                          ,  'UKR'     ,  380     , 3);
INSERT INTO `Country` VALUES(209,'AE','United Arab Emirates'                            , 'الإمارات العربية المتحدة'                          ,  'ARE'     ,  971     , 2);
INSERT INTO `Country` VALUES(210,'US','United States'                                   , 'الولايات المتحدة'                                  ,  'USA'     ,  1       , 4);
INSERT INTO `Country` VALUES(211,'UY','Uruguay'                                         , 'أورغواي'                                           ,  'URY'     ,  598      , 5);
INSERT INTO `Country` VALUES(212,'UZ','Uzbekistan'                                      , 'أوزباكستان'                                        ,  'UZB'     ,  998      , 2);
INSERT INTO `Country` VALUES(213,'VU','Vanuatu'                                         , 'فانواتو'                                           ,  'VUT'     ,  678      , 6);
INSERT INTO `Country` VALUES(214,'VE','Venezuela'                                       , 'فنزويلا'                                            ,  'VEN'     ,  58       , 5);
INSERT INTO `Country` VALUES(215,'VN','Vietnam'                                         , 'فيتنام'                                            ,  'VNM'     ,  84       , 2);
INSERT INTO `Country` VALUES(216,'VI','Virgin Islands (U.S.)'                           , 'الجزر العذراء الأمريكي'                            ,  'VIR'     ,  1340     , 4);
INSERT INTO `Country` VALUES(217,'WL','Wales'                                           , 'ويلز'                                              ,  'Wal'     ,  44        , 3);
INSERT INTO `Country` VALUES(218,'EH','Western Sahara'                                  , 'الصحراء الغربية'                                  ,  'ESH'    ,  212        , 1);
INSERT INTO `Country` VALUES(219,'YE','Yemen'                                           , 'اليمن'                                             ,  'YEM'     ,  967       , 2);
INSERT INTO `Country` VALUES(220,'ZM','Zambia'                                          , 'زامبيا'                                            ,  'ZMB'      ,  260      , 1);
INSERT INTO `Country` VALUES(221,'ZW','Zimbabwe'                                        , 'زمبابوي'                                           ,  'ZWE'      ,  263      , 1);



INSERT INTO `Position_Category` VALUES(1, 'Goalkeeper'  , 'حارس مرمى');
INSERT INTO `Position_Category` VALUES(2, 'Defender'    , 'مدافع');
INSERT INTO `Position_Category` VALUES(3, 'Midfielder'  , 'وسط ميدان');
INSERT INTO `Position_Category` VALUES(4, 'Forward'     , 'مهاجم');



INSERT INTO `Position` VALUES(1 , 1, 'GK' , 'Goalkeeper'              , 'حارس مرمى');
INSERT INTO `Position` VALUES(2 , 2, 'LIB', 'Libero'                  , 'ليبرو');
INSERT INTO `Position` VALUES(3 , 2, 'CB' , 'Center Back'             , 'قلب دفاع');
INSERT INTO `Position` VALUES(4 , 2, 'LB' , 'Left Back'               , 'ظهير أيسر');
INSERT INTO `Position` VALUES(5 , 2, 'RB' , 'Right Back'              , 'ظهير أيمن');
INSERT INTO `Position` VALUES(6 , 2, 'LWB', 'Left Wing Back'          , 'جناح دفاعي أيسر');
INSERT INTO `Position` VALUES(7 , 2, 'RWB', 'Right Wing Back'         , 'جناح دفاعي أيمن');
INSERT INTO `Position` VALUES(8 , 3, 'CDM', 'Defensive Midfielder'    , 'وسط دفاعي');
INSERT INTO `Position` VALUES(9 , 3, 'CM' , 'Central Midfielder'      , 'وسط');
INSERT INTO `Position` VALUES(10, 3, 'CAM', 'Attacking Midfielder'    , 'وسط هجومي');
INSERT INTO `Position` VALUES(11, 3, 'LM' , 'Left Midfielder'         , 'وسط أيسر');
INSERT INTO `Position` VALUES(12, 3, 'RM' , 'Right Midfielder'        , 'وسط أيمن');
INSERT INTO `Position` VALUES(13, 4, 'LW' , 'Left Winger'             , 'جناح أيسر');
INSERT INTO `Position` VALUES(14, 4, 'RW' , 'Right Winger'            , 'جناح أيمن');
INSERT INTO `Position` VALUES(15, 4, 'SS' , 'Second Striker'          , 'مهاجم متأخر');
INSERT INTO `Position` VALUES(16, 4, 'CF' , 'Center Forward'          , 'قلب هجوم');



INSERT INTO `Formation` VALUES(1 , '3-4-3'   , NULL);
INSERT INTO `Formation` VALUES(2 , '3-5-2'   , NULL);
INSERT INTO `Formation` VALUES(3 , '4-2-3-1' , NULL);
INSERT INTO `Formation` VALUES(4 , '4-3-3'   , NULL);
INSERT INTO `Formation` VALUES(5 , '4-3-3'   , 'Offensive');
INSERT INTO `Formation` VALUES(6 , '4-3-3'   , 'Defensive');
INSERT INTO `Formation` VALUES(7 , '4-3-3'   , 'Libero');
INSERT INTO `Formation` VALUES(8 , '4-4-2'   , NULL);
INSERT INTO `Formation` VALUES(9 , '4-4-2'   , 'Flat');
INSERT INTO `Formation` VALUES(10, '4-4-2'   , 'Diamond');
INSERT INTO `Formation` VALUES(11, '4-4-2'   , 'Double Pivot');
INSERT INTO `Formation` VALUES(12, '4-5-1'   , NULL);
INSERT INTO `Formation` VALUES(13, '5-2-3'   , NULL);
INSERT INTO `Formation` VALUES(14, '5-3-2'   , NULL);
INSERT INTO `Formation` VALUES(15, '5-4-1'   , NULL);

