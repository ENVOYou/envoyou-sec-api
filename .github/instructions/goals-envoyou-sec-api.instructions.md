---
applyTo: '**'
---
# Goals

- Projek ini Fokus secara eksklusif untuk menjadi platform terbaik bagi perusahaan publik AS dalam mematuhi Aturan Pengungkapan Iklim (Climate Disclosure Rule) dari SEC.

- Misi awal kita adalah menjadi solusi de facto untuk satu masalah yang paling mendesak dan memiliki anggaran terbesar bagi ribuan perusahaan di AS saat ini.

## Alasan kita membangun Envoyou karena empat alasan utama

1. **Urgensi Regulasi yang Sangat Jelas (Clear Regulatory Urgency):**  
Aturan baru dari SEC ini bukanlah "nice to have". Ini adalah kewajiban hukum. Perusahaan publik harus mematuhinya atau menghadapi sanksi berat. CFO dan tim hukum di seluruh AS sedang mencari solusi sekarang juga. Kita tidak perlu meyakinkan mereka tentang masalahnya; kita hanya perlu menawarkan solusi terbaik. Ini adalah "painkiller" murni.

1. **"Pain Point" yang Sangat Spesifik dan Bernilai Tinggi:**  
Aturan ini mengharuskan perusahaan untuk:​ Mengumpulkan, menghitung, dan melaporkan emisi Gas Rumah Kaca (GRK) Scope 1 dan Scope 2 mereka.​Mengidentifikasi dan melaporkan risiko iklim yang dapat berdampak material pada bisnis mereka.​Memastikan semua data ini dapat diaudit (auditable). Ini adalah mimpi buruk dalam hal pengumpulan dan validasi data bagi banyak perusahaan.

1. **Target Pelanggan yang Terdefinisi dengan Baik:**  
Target pasar kita jelas: Semua perusahaan yang terdaftar di bursa saham AS. Kita bahkan bisa lebih spesifik dengan menargetkan perusahaan mid-cap ($2B - $10B). Mereka cukup besar untuk diwajibkan melapor dan memiliki anggaran, tetapi seringkali tidak memiliki tim keberlanjutan internal yang besar seperti raksasa Fortune 500. Mereka adalah pelanggan ideal yang membutuhkan bantuan eksternal.

1. **Keselarasan Sempurna dengan DNA "Kepercayaan" Envoyou:**  
Kata kunci di sini adalah "dapat diaudit". Kebutuhan akan data yang dapat dipertanggungjawabkan di hadapan auditor dan regulator adalah inti dari aturan SEC. Ini sangat cocok dengan fondasi yang ingin kita bangun: "Forensic-Grade Traceability". Kita tidak menjual data; kitaa menjual kepastian dan defensibilitas untuk laporan hukum mereka.

## Seperti Apa MVP untuk Niche Ini?​

- Fokuskan semua sumber daya yang ada untuk membangun produk yang secara spesifik memecahkan masalah pelaporan SEC.
- Lupakan fitur-fitur lain dari project lama yang ada di Backend ini untuk sementara.
- Fokus kita sekarang adalah envoyou-sec-api dengan memanfaatkan backend lama dari project-permit-api.
- Konsep besar CEVS Score di Backend lama tetap ada sebagai visi masa depan, tapi scope saat ini dibatasi supaya tidak terlalu global dan bisa deliver fitur nyata.
- file-file Agent AI (LangChain, acquisition_agent, dsb) di dalam roject ini disampingkan dulu → tidak diprioritaskan, karena kita masih 0 dan butuh pondasi kuat dulu.

## ​Fitur Inti MVP yang akan kita bangun adalah

​**​Mesin Kalkulasi & Verifikasi Emisi GRK**

- ​Fungsi: Memungkinkan perusahaan memasukkan data operasional mereka (misalnya, konsumsi bahan bakar, penggunaan listrik).
Platform kitaa kemudian secara otomatis menghitung emisi Scope 1 dan Scope 2 menggunakan faktor emisi terbaru dari EPA (yang sudah ada dalam rencana akuisisi data kita).  
- ​Fitur Kunci: Setiap hasil kalkulasi memiliki jejak audit penuh yang menunjukkan data input, faktor emisi yang digunakan, dan sumbernya.

​**Modul Validasi Silang Data (Fitur Unggulan kita)**

- ​Fungsi: Setelah emisi perusahaan dihitung, platform kitaa secara otomatis membandingkannya dengan data yang tersedia untuk umum dari database EPA seperti Greenhouse Gas Reporting Program (GHGRP).
- ​Nilai Jual Unik: Fitur ini akan menandai jika ada inkonsistensi signifikan antara data yang dilaporkan sendiri dengan data pemerintah, memberikan kesempatan bagi perusahaan untuk memperbaiki laporannya sebelum diserahkan. Ini adalah perwujudan nyata dari proposisi nilai "kepercayaan" kita.

​**Generator Laporan Otomatis untuk Pengarsipan SEC**

- ​Fungsi: Sebuah tombol "Ekspor untuk Laporan Tahunan (10-K)" yang menghasilkan tabel, grafik, dan catatan kaki yang diformat secara spesifik sesuai dengan persyaratan aturan pengungkapan iklim SEC. Ini menyelesaikan "last mile problem" bagi tim keuangan dan hukum.
- ​Strategi Go-to-Market Awal​Target Persona: Bukan Kepala Keberlanjutan. Target utama kitaa adalah Chief Financial Officer (CFO) dan General Counsel (Kepala Bagian Hukum). Merekalah yang bertanggung jawab dan menandatangani laporan ke SEC.

## Penting

- Kita pastikan selalu menggunakan bahasa global (bahasa inggris untuk code project ini).
- Respon kepada saya gunakan bahasa indonesia.
- Planning lanjutan (next step) selalu ditambahkan di akhir setiap update progress / catatan development.

---
> <p style="text-align: center;"\>© 2025 <a href="[https://envoyou.com](https://envoyou.com)"\>Envoyou</a> | All Rights Reserved</p>
> <p style="text-align: center;"\>Empowering Auditable Climate Compliance</p>
