import customtkinter as ctk
import cv2
from PIL import Image
import os
import threading
import math

# Forzamos modo oscuro
ctk.set_appearance_mode("dark")

class PotatoGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Configuración de Pantalla Completa y FORZADO de Negro Absoluto
        self.attributes("-fullscreen", True)
        self.configure(fg_color="#000000")
        self.bind("<Escape>", lambda e: self.cerrar_programa())

        # Layout principal: Izquierda (Consola), Centro (Esfera), Derecha (Espacio/Info)
        self.grid_columnconfigure(0, weight=1) # Consola
        self.grid_columnconfigure(1, weight=2) # Esfera
        self.grid_columnconfigure(2, weight=1) # Espacio/Info
        self.grid_rowconfigure(0, weight=1)    # Contenido principal
        self.grid_rowconfigure(1, weight=0)    # Entrada de texto

        # 2. Consola de Comandos (Izquierda)
        self.consola = ctk.CTkTextbox(
            self, 
            fg_color="#000000", 
            text_color="#ffffff", # blanco
            font=ctk.CTkFont(family="Courier", size=14),
            border_width=1,
            border_color="#333333"
        )
        self.consola.grid(row=0, column=0, padx=20, pady=50, sticky="nsew")
        self.log_consola(">>> SISTEMA POTATO INICIALIZADO...")

        # 3. Contenedor Central para la Esfera
        self.main_frame = ctk.CTkFrame(self, fg_color="#000000")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        
        # Centrar contenido dentro del main_frame
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)

        # Canvas para la visualización dinámica de la esfera
        self.canvas_size = 400
        self.canvas = ctk.CTkCanvas(
            self.main_frame, 
            width=self.canvas_size, 
            height=self.canvas_size, 
            bg="#000000", 
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, pady=(100, 0))

        # Etiqueta de Estado
        self.estado_label = ctk.CTkLabel(
            self.main_frame, text="SISTEMA ONLINE", 
            font=ctk.CTkFont(family="Courier", size=20, weight="bold"),
            text_color="#F7BE02",
            fg_color="#000000"
        )
        self.estado_label.grid(row=1, column=0, pady=30)

        # 4. Entrada de Chat (Abajo)
        self.input_frame = ctk.CTkFrame(self, fg_color="#000000", height=60)
        self.input_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=20, pady=20)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_chat = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Escribe aquí para confirmar o hablar con Potato...",
            fg_color="#111111",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Courier", size=16),
            border_color="#333333"
        )
        self.input_chat.grid(row=0, column=0, sticky="ew", padx=(10, 10), pady=10)
        self.input_chat.bind("<Return>", self.procesar_input_chat)

        # Evento para esperar confirmación
        self.input_confirmacion = None
        self.evento_confirmacion = threading.Event()

        # 5. Inicializar variables para la esfera dinámica
        self.audio_volume = 0.0
        self.audio_bass = 0.0
        self.audio_mid = 0.0
        self.audio_treble = 0.0
        self.anim_phase = 0.0
        self.estado = "SISTEMA ONLINE"
        
        # Iniciar bucle de animación
        self.animar_canvas()

    def log_consola(self, texto):
        """Añade texto a la consola lateral de forma segura (Thread-safe)"""
        self.after(0, self._log_consola_main, texto)

    def _log_consola_main(self, texto):
        self.consola.insert("end", f"{texto}\n")
        self.consola.see("end")

    def cambiar_estado(self, nuevo_texto):
        """Cambia el texto de estado de forma segura (Thread-safe)"""
        def update():
            self.estado_label.configure(text=nuevo_texto)
            self.estado = nuevo_texto
        self.after(0, update)

    def procesar_input_chat(self, event):
        """Maneja el texto introducido en el entry"""
        texto = self.input_chat.get().strip()
        if texto:
            self.log_consola(f"USUARIO: {texto}")
            self.input_chat.delete(0, "end")
            
            # Si estamos esperando una confirmación, liberamos el evento
            if not self.evento_confirmacion.is_set():
                self.input_confirmacion = texto.lower()
                self.evento_confirmacion.set()

    def esperar_confirmacion_chat(self, timeout=30):
        """Espera a que el usuario escriba algo en el chat"""
        self.evento_confirmacion.clear()
        self.input_confirmacion = None
        # Esperar hasta que se setee el evento (desde procesar_input_chat)
        confirmado = self.evento_confirmacion.wait(timeout=timeout)
        if confirmado:
            return self.input_confirmacion
        return ""

    def update_audio_metrics(self, volume, frequencies=None):
        """Actualiza el volumen y las frecuencias para la animación dinámica"""
        self.audio_volume = volume
        if frequencies is not None:
            self.audio_bass, self.audio_mid, self.audio_treble = frequencies
        else:
            self.audio_bass = volume * 0.5
            self.audio_mid = volume * 0.3
            self.audio_treble = volume * 0.2

    def _blend_colors(self, bg_hex, fg_hex, alpha):
        """Mezcla un color hexadecimal con el color de fondo usando un valor alpha (0.0 - 1.0)"""
        bg_hex = bg_hex.lstrip('#')
        fg_hex = fg_hex.lstrip('#')
        
        bg_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (0, 2, 4))
        fg_rgb = tuple(int(fg_hex[i:i+2], 16) for i in (0, 2, 4))
        
        blended_rgb = tuple(
            int(bg_rgb[i] * (1 - alpha) + fg_rgb[i] * alpha)
            for i in range(3)
        )
        return f"#{blended_rgb[0]:02x}{blended_rgb[1]:02x}{blended_rgb[2]:02x}"

    def animar_canvas(self):
        # Limpiar canvas
        self.canvas.delete("all")
        
        cx = self.canvas_size // 2
        cy = self.canvas_size // 2
        
        # Dependiendo del estado del asistente, cambiamos colores, radios y velocidades
        estado = self.estado.upper()
        
        if "CALIBRANDO" in estado:
            color_principal = "#F7BE02"  # Amarillo/Oro
            color_secundario = "#ff8800"
            r_base = 75
            deformacion_base = 6
            freq_onda = 4.0
            velocidad = 0.05
        elif "ESCUCHANDO" in estado:
            color_principal = "#00e5ff"  # Cyan eléctrico
            color_secundario = "#0055ff"  # Azul profundo
            r_base = 85
            deformacion_base = 12
            freq_onda = 5.0
            velocidad = 0.12
        elif "PROCESANDO" in estado:
            color_principal = "#d500f9"  # Magenta eléctrico
            color_secundario = "#7c4dff"  # Púrpura
            r_base = 80
            deformacion_base = 18
            freq_onda = 8.0  # Mucho oleaje
            velocidad = 0.22  # Rápido
        elif "RESPONDIENDO" in estado:
            color_principal = "#ffea00"  # Amarillo neón
            color_secundario = "#ff5500"  # Naranja brillante
            r_base = 80
            # Altamente reactivo al volumen del audio de voz
            deformacion_base = 5 + self.audio_volume * 110
            freq_onda = 3.0 + self.audio_volume * 12.0
            velocidad = 0.08 + self.audio_volume * 0.35
        else:  # SISTEMA ONLINE / IDLE
            color_principal = "#F7BE02"  # Amarillo / Oro
            color_secundario = "#ff6f00"  # Naranja
            r_base = 80
            deformacion_base = 3
            freq_onda = 2.0
            velocidad = 0.04
            
        self.anim_phase += velocidad
        
        # 1. Dibujar Glow de fondo (resplandor difuminado)
        resplandor_max = 25 + (self.audio_volume * 60 if "RESPONDIENDO" in estado else deformacion_base * 1.5)
        for i in range(5, 0, -1):
            r_glow = r_base + resplandor_max * (i / 5.0)
            alpha_color = self._blend_colors("#000000", color_principal, 0.04 * (6 - i))
            self.canvas.create_oval(
                cx - r_glow, cy - r_glow, 
                cx + r_glow, cy + r_glow, 
                fill=alpha_color, outline=""
            )
            
        # 2. Dibujar Ondas Dinámicas (3 anillos entrelazados con desfases)
        num_anillos = 3
        num_puntos = 64
        
        for ring_idx in range(num_anillos):
            puntos = []
            r_ring = r_base - ring_idx * 7
            
            # Rotaciones e interferencias asimétricas
            fase_anillo = self.anim_phase * (1.0 - ring_idx * 0.2) + (ring_idx * math.pi / 2.0)
            direccion = -1 if ring_idx % 2 == 0 else 1
            fase_anillo *= direccion
            
            if ring_idx == 0:
                color_anillo = color_principal
                ancho = 3
                amp_anillo = deformacion_base
            elif ring_idx == 1:
                color_anillo = color_secundario
                ancho = 2
                amp_anillo = deformacion_base * 0.75
            else:
                color_anillo = "#ffffff"
                ancho = 1.5
                amp_anillo = deformacion_base * 0.45
                
            for i in range(num_puntos + 1):
                angulo = (i / num_puntos) * 2 * math.pi
                # Variar amplitud según el ángulo para deformación orgánica no simétrica
                amp_angulo = amp_anillo * (1.0 + 0.3 * math.sin(3.0 * angulo + fase_anillo))
                r = r_ring + amp_angulo * math.sin(freq_onda * angulo + fase_anillo)
                x = cx + r * math.cos(angulo)
                y = cy + r * math.sin(angulo)
                puntos.append((x, y))
                
            # Dibujar la línea curva usando create_line con suavizado
            for i in range(len(puntos) - 1):
                self.canvas.create_line(
                    puntos[i][0], puntos[i][1], 
                    puntos[i+1][0], puntos[i+1][1], 
                    fill=color_anillo, width=ancho, smooth=True
                )
                
        # 3. Dibujar Esfera/Núcleo Central
        pulso_core = 2.5 * math.sin(self.anim_phase)
        r_core = 30 + (self.audio_volume * 35 if "RESPONDIENDO" in estado else pulso_core)
        
        # Núcleo concéntrico sólido
        self.canvas.create_oval(
            cx - r_core, cy - r_core,
            cx + r_core, cy + r_core,
            fill=color_principal, outline=""
        )
        self.canvas.create_oval(
            cx - r_core * 0.65, cy - r_core * 0.65,
            cx + r_core * 0.65, cy + r_core * 0.65,
            fill="#ffffff", outline=""
        )

        # Solicitar siguiente frame a 33 FPS (~30ms)
        self.after(30, self.animar_canvas)

    def cerrar_programa(self):
        self.destroy()

if __name__ == "__main__":
    app = PotatoGUI()
    app.mainloop()
