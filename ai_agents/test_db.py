import os
from db import ChatDB

def main():
    print("=== 🧠 ChatDB Test Utility ===\n")

    # Initialize DB
    db = ChatDB()
    print(f"📁 Using DB file: {db.db_path}\n")

    # 1️⃣ Insert sample chats
    #print("➡️ Inserting sample chat records...")
    #chat1_id = db.add_chat("What is microservices architecture?", "UnderstandingAgent", "Explained microservices concept.")
    #chat2_id = db.add_chat("Generate documentation for API layer.", "DocGeneratorAgent", "Documentation created successfully.")
    #chat3_id = db.add_chat("Assess impact of new payment feature.", "ImpactAnalyzerAgent", "Impact analysis completed.")

    #print(f"✅ Inserted records with IDs: {chat1_id}, {chat2_id}, {chat3_id}\n")

    # 2️⃣ Fetch all chats
    print("📜 All chat records (latest first):")
    all_chats = db.get_all_chats()
    for row in all_chats:
        print(f"  - ID: {row[0]}, Agent: {row[2]}, Query: {row[1][:40]}..., Created: {row[4]}")
    print()

    # 3️⃣ Fetch by specific ID
    if all_chats:
        last_id = all_chats[0][0]
        print(f"🔍 Fetching details for chat_id={last_id}")
        chat = db.get_chat_by_id(last_id)
        if chat:
            print("\n🧾 Chat Details:")
            print(f"ID: {chat[0]}")
            print(f"User Query: {chat[1]}")
            print(f"Agent: {chat[2]}")
            print(f"Response: {chat[3][:200]}...")
            print(f"Created At: {chat[4]}")
    else:
        print("⚠️ No chats found in DB.")

    # 4️⃣ Show DB location for manual inspection
    print(f"\n📍 You can inspect the DB file manually here:\n   {os.path.abspath(db.db_path)}\n")

if __name__ == "__main__":
    main()
