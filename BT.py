import requests
from bs4 import BeautifulSoup
import pandas as pd
import schedule
import time
from datetime import datetime

# Header để giả lập trình duyệt
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
}

# Lấy thông tin chi tiết từ 1 trang việc làm cụ thể
def get_job_data(url):
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        title_tag = soup.find("h1", class_="title font-roboto text-primary")
        title = title_tag.find("span", class_="text").text.strip() if title_tag else "Không có tiêu đề"

        paragraphs = soup.find_all("p")
        company = salary = location = description = "Không rõ"
        for p in paragraphs:
            text = p.get_text(strip=True)
            if "Công ty" in text and company == "Không rõ":
                company = text
            elif "Lương" in text and salary == "Không rõ":
                salary = text
            if "Địa chỉ làm việc" in text:
                location = text.split("Địa chỉ làm việc:")[-1].strip()
            elif "Mô tả" in text or "công việc" in text.lower():
                description = text

        return [{
            "Tiêu đề": title,
            "Mô tả": description,
            "Công ty": company,
            "Lương": salary,
            "Địa chỉ làm việc": location
        }]
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu từ {url}: {e}")
        return []

# Lấy danh sách việc làm từ bảng danh sách
def get_jobs_from_custom_table(url):
    job_list = []
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for row in soup.select("tr"):
            title_td = row.select_one("td.block-item.w55")
            others = row.select("td.text-center.w15")

            if title_td and len(others) >= 2:
                info = title_td.get_text("\n", strip=True).split("\n")
                job_list.append({
                    "Vị trí tuyển dụng": info[0] if len(info) > 0 else "Không rõ",
                    "Tên công ty": info[1] if len(info) > 1 else "Không rõ",
                    "Địa điểm": others[0].text.strip(),
                    "Hạn nộp": others[1].text.strip(),
                    "URL": url
                })
    except Exception as e:
        print(f"Lỗi khi xử lý {url}: {e}")
    return job_list

# Hàm chính: tổng hợp dữ liệu và lưu file Excel
def main():
    all_jobs = []

    # Dữ liệu từ 1 tin chi tiết
    detail_url = "https://www.danang43.vn/viec-lam/nhan-vien-thiet-ke-designer-3-p69103.html"
    all_jobs.extend(get_job_data(detail_url))

    # Dữ liệu từ danh sách nhiều trang
    list_urls = [
        "https://www.danang43.vn/nganh-nghe/quang-cao-marketing-pr",
        "https://www.danang43.vn/nganh-nghe/quang-cao-marketing-pr/page/2",
        "https://www.danang43.vn/nganh-nghe/quang-cao-marketing-pr/page/3"
    ]

    for url in list_urls:
        print(f"Đang lấy dữ liệu từ: {url}")
        all_jobs.extend(get_jobs_from_custom_table(url))

    # Ghi file Excel
    if all_jobs:
        filename = f"danang43_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        pd.DataFrame(all_jobs).to_excel(filename, index=False)
        print(f"Đã lưu {len(all_jobs)} công việc vào '{filename}'")
    else:
        print("Không có dữ liệu để lưu.")

# Tự động chạy mỗi ngày lúc 6h sáng
schedule.every().day.at("06:00").do(main)

if __name__ == "__main__":
    print("Chạy kiểm thử ngay lập tức...")
    main()  # <-- chạy ngay để test
    print("Đang chờ đến 6h sáng hàng ngày để thu thập dữ liệu...")
    while True:
        schedule.run_pending()
        time.sleep(60)
