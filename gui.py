import customtkinter as ctk
import cv2
from PIL import Image
import os

# Forzamos modo oscuro
ctk.set_appearance_mode("dark")

class JarvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Configuración de Pantalla Completa y FORZADO de Negro Absoluto en la raíz
        self.attributes("-fullscreen", True)
        self.configure(fg_color="#000000")  # <-- Esto arregla el fondo gris exterior
        self.bind("<Escape>", lambda e: self.cerrar_programa())

        # 2. Contenedor Principal Centrado en Negro Absoluto
        self.main_frame = ctk.CTkFrame(self, fg_color="#000000")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # 3. Etiqueta para renderizar el Video
        self.video_size = 400
        self.video_label = ctk.CTkLabel(self.main_frame, text="", fg_color="#000000")
        self.video_label.pack()

        # 4. Etiqueta de Estado de Jarvis
        self.estado_label = ctk.CTkLabel(
            self.main_frame, text="SISTEMA ONLINE", 
            font=ctk.CTkFont(family="Courier", size=20, weight="bold"),
            text_color="#00e5ff",
            fg_color="#000000"
        )
        self.estado_label.pack(pady=30)

        # 5. Cargar el Video
        self.ruta_video = "video-audio/jarvis_sphere.mp4"
        if not os.path.exists(self.ruta_video):
            print(f"[Error]: No se encontró el video en la ruta: {self.ruta_video}")
            self.cap = None
        else:
            self.cap = cv2.VideoCapture(self.ruta_video)
            self.actualizar_video()

    def actualizar_video(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()

            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(frame_rgb)
                
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(self.video_size, self.video_size))
                
                self.video_label.configure(image=img_ctk)
                self.video_label.image = img_ctk 

        self.after(30, self.actualizar_video)

    def cambiar_estado(self, nuevo_texto):
        self.estado_label.configure(text=nuevo_texto)

    def cerrar_programa(self):
        if self.cap is not None:
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = JarvisGUI()
    app.mainloop()