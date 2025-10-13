from get_msg import get_all_msg

def main():
    first_msg, most_common_100 = get_all_msg()
    print(f"1 сообщение - {first_msg}")
    print("Топ-100 самых частых русских слов:")
    print("=" * 45)
    for i, (word, count) in enumerate(most_common_100, 1):
        print(f"{i:2d}. '{word}' - {count} раз")
        
        
if __name__ == "__main__":
    main()