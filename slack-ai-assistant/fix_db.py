import sqlite3

def fix_db():
    conn = sqlite3.connect('slack_data.db')
    cursor = conn.cursor()
    # Any old name will just be replaced by the ID for testing purposes today
    cursor.execute("UPDATE messages SET user_id = '<@U09CXFRKMHU>' WHERE user_id NOT LIKE '<@%'")
    conn.commit()
    conn.close()
    print("DB Updated!")

if __name__ == '__main__':
    fix_db()
