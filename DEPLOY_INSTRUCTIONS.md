# Render এ প্রজেক্ট হোস্ট করার নিয়ম (Web App)

আপনার প্রজেক্টটি এখন একটি **ওয়েব অ্যাপ** হিসেবে কনফিগার করা হয়েছে।

নিচের ধাপগুলো অনুসরণ করুন:

১. **GitHub এ কোড আপডেট:**
   - আমি সব ফাইল আপডেট করে দিয়েছি। GitHub এ কোডগুলো অটোমেটিকভাবে আপলোড হয়ে যাবে।

২. **Render Service Settings:**
   - Render Dashboard এ যান এবং আপনার সার্ভিসে ক্লিক করুন।
   - **Settings** এ যান।
   - **Start Command** বক্সটি **পুরোপুরি খালি (Empty)** রাখুন। (Gunicorn অটোমেটিক চালু হবে Dockerfile এর মাধ্যমে)।
   - **Environment Variables** এ গিয়ে একটি নতুন Variable যোগ করুন (যদি লাগে, তবে বর্তমানে কিছু লাগছে না)।

৩. **Redeploy:**
   - **Manual Deploy** -> **Deploy latest commit** এ ক্লিক করুন।

৪. **Web Interface ব্যবহার:**
   - ডিপ্লয় শেষ হলে Render এর দেওয়া URL এ যান (যেমন: `https://your-service.onrender.com`)।
   - সেখানে একটি বক্স দেখবেন "Enter Numbers"।
   - নাম্বারগুলো বসিয়ে **Start Bot** এ ক্লিক করুন।
   - নিচে Log দেখতে পাবেন।

কোনো সমস্যা হলে জানাবেন!
