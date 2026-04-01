import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import ImageTk, Image
import datetime

from config import CAMERA_ID
from data_collector import DataCollector
from attendance_core import AttendanceCore


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("人脸签到系统")
        self.geometry("1200x800")
        self.dc = DataCollector()
        self.ac = AttendanceCore()
        self.cap = None
        self.running = False
        self.has_shown_success = False
        self.build_ui()

    def build_ui(self):
        title = tk.Label(self, text="人脸签到系统", font=("Arial", 20, "bold"))
        title.pack(pady=10)

        tab = ttk.Notebook(self)
        self.tab1 = ttk.Frame(tab)
        self.tab2 = ttk.Frame(tab)
        self.tab3 = ttk.Frame(tab)
        self.tab4 = ttk.Frame(tab)
        tab.add(self.tab1, text="采集")
        tab.add(self.tab2, text="签到/签退")
        tab.add(self.tab3, text="记录")
        tab.add(self.tab4, text="成员管理")
        tab.pack(expand=1, fill="both", padx=10, pady=10)

        # 采集
        f1 = ttk.Frame(self.tab1)
        f1.pack(pady=20)
        ttk.Label(f1, text="学号").grid(row=0, column=0, padx=5)
        self.sid = ttk.Entry(f1)
        self.sid.grid(row=0, column=1, padx=5)
        ttk.Label(f1, text="姓名").grid(row=0, column=2, padx=5)
        self.name = ttk.Entry(f1)
        self.name.grid(row=0, column=3, padx=5)
        ttk.Button(self.tab1, text="采集", command=self.do_collect).pack(pady=5)
        ttk.Button(self.tab1, text="注册", command=self.do_reg).pack(pady=5)

        # 签到签退
        self.vid = tk.Label(self.tab2)
        self.vid.pack(expand=1, fill="both", padx=30, pady=20)
        self.msg = ttk.Label(self.tab2, font=("", 16, "bold"))
        self.msg.pack(pady=10)
        f2 = ttk.Frame(self.tab2)
        f2.pack(pady=10)
        ttk.Button(f2, text="签到", command=self.start_checkin).grid(row=0, column=0, padx=10)
        ttk.Button(f2, text="签退", command=self.start_checkout).grid(row=0, column=1, padx=10)
        ttk.Button(f2, text="停止", command=self.stop).grid(row=0, column=2, padx=10)

        # 记录
        ttk.Button(self.tab3, text="刷新", command=self.refresh_records).pack(pady=5)
        ttk.Button(self.tab3, text="重置签到", command=self.reset_all).pack(pady=5)
        cols = ("sid", "name", "time", "status")
        self.tree = ttk.Treeview(self.tab3, columns=cols, show="headings")
        for c, t in zip(cols, ["学号", "姓名", "时间", "状态"]):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=200)
        self.tree.pack(expand=1, fill="both", padx=30)

        # 成员管理
        f4 = ttk.Frame(self.tab4)
        f4.pack(pady=10)
        ttk.Button(f4, text="刷新成员", command=self.refresh_members).grid(row=0, column=0, padx=10)
        ttk.Button(f4, text="删除选中", command=self.delete_member).grid(row=0, column=1, padx=10)
        ttk.Button(f4, text="清空所有成员", command=self.clear_all_members).grid(row=0, column=2, padx=10)

        self.mem_tree = ttk.Treeview(self.tab4, columns=("sid", "name", "status"), show="headings")
        for c, t in zip(("sid", "name", "status"), ["学号", "姓名", "状态"]):
            self.mem_tree.heading(c, text=t)
            self.mem_tree.column(c, width=250)
        self.mem_tree.pack(expand=1, fill="both", padx=30, pady=10)

        self.refresh_members()

    def do_collect(self):
        sid = self.sid.get().strip()
        name = self.name.get().strip()
        if not sid or not name:
            messagebox.showerror("错误", "学号和姓名不能为空！")
            return
        ok = self.dc.collect(sid, name)
        if ok:
            messagebox.showinfo("成功", "采集完成！")

    def do_reg(self):
        sid = self.sid.get().strip()
        name = self.name.get().strip()
        if not sid or not name:
            messagebox.showerror("错误", "学号和姓名不能为空！")
            return
        feat = self.dc.get_avg_feature(sid, name)
        if feat is None:
            messagebox.showerror("错误", "请先完成人脸采集！")
            return
        ok, msg = self.ac.db.add_student(sid, name, feat)
        if ok:
            self.ac.load()
            self.refresh_members()
            messagebox.showinfo("成功", msg)
        else:
            messagebox.showerror("失败", msg)

    def start_checkin(self):
        self.ac.set_mode("checkin")
        self.start_camera()

    def start_checkout(self):
        self.ac.set_mode("checkout")
        self.start_camera()

    def start_camera(self):
        self.cap = cv2.VideoCapture(CAMERA_ID)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.running = True
        self.has_shown_success = False
        self.update_frame()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.vid.config(image="", text="已停止")
        self.msg.config(text="已停止")

    def update_frame(self):
        if not self.running:
            return
        ret, frm = self.cap.read()
        if ret:
            out, msg = self.ac.run(frm)
            self.msg.config(text=msg)

            if ("签到完成" in msg or "签退完成" in msg) and not self.has_shown_success:
                self.has_shown_success = True
                messagebox.showinfo("成功", msg)
                self.refresh_records()
                self.refresh_members()

            rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(rgb)
            tkimg = ImageTk.PhotoImage(image=im)
            self.vid.imgtk = tkimg
            self.vid.config(image=tkimg)
        self.after(10, self.update_frame)

    def refresh_records(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in self.ac.db.get_today_attendance():
            self.tree.insert("", "end", values=row)

    def refresh_members(self):
        for i in self.mem_tree.get_children():
            self.mem_tree.delete(i)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        for sid, name in self.ac.db.get_all_students():
            status = self.ac.db.get_member_status(sid, today)
            self.mem_tree.insert("", "end", values=(sid, name, status))

    def reset_all(self):
        if messagebox.askyesno("确认", "确定重置所有签到？"):
            self.ac.db.reset_all_records()
            self.ac.signed = set()
            self.refresh_records()
            self.refresh_members()
            messagebox.showinfo("成功", "签到数据已重置！")

    def delete_member(self):
        selected = self.mem_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择成员！")
            return
        sid = self.mem_tree.item(selected[0])["values"][0]
        if messagebox.askyesno("确认", f"确定删除成员 {sid}？"):
            self.ac.db.delete_student(sid)
            self.ac.load()
            self.refresh_members()
            messagebox.showinfo("成功", "成员已删除！")

    def clear_all_members(self):
        if messagebox.askyesno("警告", "确定删除所有成员？此操作不可恢复！"):
            self.ac.db.clear_all_students()
            self.ac.load()
            self.refresh_members()
            messagebox.showinfo("成功", "所有成员已清空！")