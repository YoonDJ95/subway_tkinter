# Excel 읽기, 쓰기
import pandas as pd
import tkinter as tk
from tkinter import *
import copy
# 이미지
from PIL import Image, ImageTk
# 자동완성 기능
import ctypes   
import re

# 엑셀 파일을 시트별로 불러오기
excel_file = r'C:\\subway_tkinter\\subway_tkinter\\subway.xlsx'
sheets = pd.read_excel(excel_file, sheet_name=None)

# 노선과 환승역 시트 분리
lines_df = {name: df for name, df in sheets.items() if name not in ['환승역','호선정보']}
transfer_df = sheets.get('환승역', pd.DataFrame())
transfer_stations = transfer_df['지하철명'].tolist()

# 호선 정보 불러오기
line_info_df = pd.read_excel(excel_file, sheet_name='호선정보')  # '호선정보' 시트에서 데이터 읽기
line_info = line_info_df.set_index('지하철명').to_dict()['노선']

# 그래프 초기화
landscape = {}
colors = {
    '1호선': '#F66130',
    '2호선': '#27AF1D',
    '3호선': '#B58941',
    '4호선': '#286CD3',
    '동해선': '#4DCAF8',
    '부김선': '#AF49CC',
    '환승역': '#FFFFFF'
}
station_colors = {}
line_mapping = {}  # 각 역의 노선 저장

# 노선 데이터로 그래프 엣지 추가
for sheet_name, data in lines_df.items():
    color = colors.get(sheet_name, '#000000')
    for i in range(len(data) - 1):
        station1 = data.iloc[i]['지하철명']
        station2 = data.iloc[i + 1]['지하철명']
        x1, y1 = data.iloc[i]['X'], data.iloc[i]['Y']
        x2, y2 = data.iloc[i + 1]['X'], data.iloc[i + 1]['Y']

        if station1 not in landscape:
            landscape[station1] = {}
        if station2 not in landscape:
            landscape[station2] = {}

        landscape[station1][station2] = 1
        landscape[station2][station1] = 1
        
        # 노선 매핑 추가
        if station1 not in line_mapping:
            line_mapping[station1] = set()
        if station2 not in line_mapping:
            line_mapping[station2] = set()
        line_mapping[station1].add(sheet_name)
        line_mapping[station2].add(sheet_name)
        
        # 역에 대한 노선별 색상 저장 (여러 노선에 속한 역일 경우 첫 번째 노선 색상 사용)
        if station1 not in station_colors:
            station_colors[station1] = color
        if station2 not in station_colors:
            station_colors[station2] = color

# 환승역 추가
for i in range(len(transfer_df)):
    station1 = transfer_df.iloc[i]['노선1']
    station2 = transfer_df.iloc[i]['노선2']
    if station1 not in landscape:
        landscape[station1] = {}
    if station2 not in landscape:
        landscape[station2] = {}
    landscape[station1][station2] = 2
    landscape[station2][station1] = 2
 


# tkinter 창 생성
root = tk.Tk()
root.title("지하철 노선도")

imm32 = ctypes.WinDLL('imm32')


# 이미지 로드 및 크기 조정 함수
def load_image(file_path, size):
    image = Image.open(file_path)
    image = image.resize(size, Image.LANCZOS)  # 이미지 크기 조정
    return ImageTk.PhotoImage(image)

# 이미지 로드
start_image_path = r"C:\\subway_tkinter\\subway_tkinter\\image\\start_495499.png"
end_image_path = r"C:\\subway_tkinter\\subway_tkinter\\image\\end_12366677.png"
trans_image_path = r"C:\\subway_tkinter\\subway_tkinter\\image\\transportation.png"
bu_image_path = r"C:\\subway_tkinter\\subway_tkinter\\image\\transportation_bu.png"
bex_image_path = r"C:\\subway_tkinter\\subway_tkinter\\image\\transportation_bex.png"
here_path = r"C:\\subway_tkinter\\subway_tkinter\\image\\here.png"

s_x_offset = 20
x_offset = 11
y_offset = 50

try:
    start_image = load_image(start_image_path, (50, 50))
    end_image = load_image(end_image_path, (50, 50))
    transfer_image = load_image(trans_image_path, (20, 20))  # 환승역 이미지 로드
    transfer_image_bu = load_image(bu_image_path, (40, 20))  # 환승역 이미지 로드
    transfer_image_bex = load_image(bex_image_path, (20, 40))  # 환승역 이미지 로드
    here_image = load_image(here_path, (20, 20))
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

def add_image(x, y, image):
    canvas.create_image(x, y, image=image, anchor=tk.NW, tags="icon")


# 출발역과 도착역을 설정하여 경로 찾기
def set_stations():
    start = start_entry.get()
    end = end_entry.get()
    if start and end:
        draw_shortest_path(start, end)

# 리셋 버튼의 콜백 함수
def reset_selection():
    global clicked_stations
    clicked_stations = []
    
    canvas.delete("icon")
    
    # 출발역과 도착역 입력 필드 비우기
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)
    
    # 총 여행 시간 및 거리 초기화
    time_label.config(text="총 여행 시간: 0 분")
    details_text.delete(1.0, tk.END)  # 기존 텍스트 삭제
    # 초기 맵 다시 그리기
    draw_map()


station_list = list(line_info.keys())  
print(station_list)

# 우측 영역에 경로 세부정보를 표시할 프레임 추가
info_frame = tk.Frame(root, padx=10, pady=10, bg='lightgrey', width=300)
info_frame.pack(side=tk.RIGHT, fill=tk.Y)

details_label = tk.Label(info_frame, text="경로 세부정보", font=("Arial", 12, "bold"), bg='lightgrey')
details_label.pack(pady=(0, 10))

details_text = tk.Text(info_frame, width=40, height=20, wrap=tk.WORD, padx=5, pady=5)
details_text.pack(expand=True)

# 입출력 및 버튼 배치
controls_frame = tk.Frame(root, padx=10, pady=10)
controls_frame.pack(side=tk.TOP, fill=tk.X)

start_label = tk.Label(controls_frame, text="출발역:")
start_label.pack(side=tk.LEFT, padx=5)
start_entry = tk.Entry(controls_frame)
start_entry.pack(side=tk.LEFT, padx=5)

# 출발역 자동완성 리스트박스
start_listbox = tk.Listbox(root)
start_listbox.pack_forget()
start_listbox.bind("<ButtonRelease-1>", lambda event: handle_click(event,start_entry, start_listbox))
start_listbox.bind("<Motion>", lambda event: update_selection_on_mouse_move(event, start_listbox))

start_entry.bind("<FocusIn>", lambda event: entry_focus_in(start_entry, start_listbox))

end_label = tk.Label(controls_frame, text="도착역:")
end_label.pack(side=tk.LEFT, padx=5)
end_entry = tk.Entry(controls_frame)
end_entry.pack(side=tk.LEFT, padx=5)

end_entry.bind("<FocusIn>", lambda event: entry_focus_in(end_entry, end_listbox))

# 도착역 자동완성 리스트박스
end_listbox = tk.Listbox(root)
end_listbox.pack_forget()
end_listbox.bind("<ButtonRelease-1>", lambda event: handle_click(event,end_entry, end_listbox))
end_listbox.bind("<Motion>", lambda event: update_selection_on_mouse_move(event, end_listbox))

set_button = tk.Button(controls_frame, text="경로 찾기", command=set_stations)
set_button.pack(side=tk.LEFT, padx=5)

reset_button = tk.Button(controls_frame, text="리셋", command=reset_selection)
reset_button.pack(side=tk.LEFT, padx=5)

time_label = tk.Label(controls_frame, text="총 여행 시간: 0 분")
time_label.pack(side=tk.LEFT, padx=5)

# 호선별 버튼을 위한 프레임 설정
line_buttons_frame = tk.Frame(controls_frame)
line_buttons_frame.pack(side=tk.RIGHT, fill=tk.X, padx=5)
line_label = tk.Label(controls_frame, text="노선정보 ▶ ", fg="blue")
line_label.pack(side=tk.RIGHT, fill=tk.X, padx=5)

# 호선별 및 편의시설 버튼을 위한 프레임 설정
button_frame = tk.Frame(root)
button_frame.pack(side=tk.TOP, fill=tk.X)

# 편의시설 버튼 프레임 설정
category_btn_frame = tk.Frame(button_frame)
category_btn_frame.pack(side=tk.RIGHT, fill=tk.X, padx=5)
category_label = tk.Label(button_frame, text="편의시설 ▶ ",fg="blue")
category_label.pack(side=tk.RIGHT, fill=tk.X, padx=5)

canvas_width = 1680
canvas_height = 900
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg='white')
canvas.pack()

clicked_stations = []  # 선택한 역을 저장할 리스트

def on_click(event):
    x, y = event.x, event.y
    for station, coord in station_positions.items():
        if abs(x - coord[0]) < 10 and abs(y - coord[1]) < 10:
            clicked_stations.append(station)
            if len(clicked_stations) == 1:
                start_entry.delete(0, tk.END)
                start_entry.insert(0, station)
                add_image(coord[0] - s_x_offset, coord[1] - y_offset, start_image)  # 조정된 위치에 출발점 이미지 추가
            elif len(clicked_stations) == 2:
                end_entry.delete(0, tk.END)
                end_entry.insert(0, station)
                add_image(coord[0] - x_offset, coord[1] - y_offset, end_image)  # 조정된 위치에 도착점 이미지 추가
                start = clicked_stations[0]
                end = clicked_stations[1]
                draw_shortest_path(start, end)
            return
        
station_positions = {}

# 노선과 역을 그리는 함수 (초기 화면 및 리셋 시 사용)
def draw_map(hidden_lines=None, highlighted_stations=None):
    canvas.delete("all")  # 기존 모든 요소 삭제
    if hidden_lines is None:
        hidden_lines = set()

    if highlighted_stations is None:
        highlighted_stations = set()

    # 환승역을 세트로 만듭니다.
    transfer_stations = set(transfer_df['지하철명'].unique())

    # 역을 표시한 세트를 만듭니다.
    displayed_stations = set()

    # 노선 그리기
    for sheet_name, data in lines_df.items():
        if sheet_name not in hidden_lines:
            color = colors[sheet_name]  # 각 노선의 색상
            for i in range(len(data) - 1):
                station1 = data.iloc[i]['지하철명']
                station2 = data.iloc[i + 1]['지하철명']
                x1, y1 = data.iloc[i]['X'], data.iloc[i]['Y']
                x2, y2 = data.iloc[i + 1]['X'], data.iloc[i + 1]['Y']
                canvas.create_line(x1, y1, x2, y2, fill=color, width=4, tags="line")

    # 역 그리기
    for sheet_name, data in lines_df.items():
        for index, row in data.iterrows():
            x, y = row['X'], row['Y']
            name = row['지하철명']
            station_positions[name] = (x, y)

            # 역 아이콘 그리기
            if name == '부전':
                if name not in displayed_stations:
                    canvas.create_image(x-10, y, image=transfer_image_bu, anchor=tk.CENTER, tags="station")
                    displayed_stations.add(name)
            elif name == '벡스코(시립미술관)':
                if name not in displayed_stations:
                    canvas.create_image(x, y, image=transfer_image_bex, anchor=tk.CENTER, tags="station")
                    displayed_stations.add(name)
            elif name in transfer_stations:
                if name not in displayed_stations:
                    canvas.create_image(x, y, image=transfer_image, anchor=tk.CENTER, tags="station")
                    displayed_stations.add(name)
            else:
                # 일반 역의 경우
                station_color = station_colors.get(name, 'black') if name not in highlighted_stations else colors.get(sheet_name, 'black')
                canvas.create_oval(x-5, y-5, x+5, y+5, fill=station_color, tags="station")
                canvas.create_text(x, y-15, text=name, fill=station_color, tags="station_name")

    # 역 이름을 선과 아이콘 위에 표시
    name_positions = {}
    for station, coord in station_positions.items():
        x, y = coord
        offset = 0
        while (x, y) in name_positions.values():
            offset += 20
            y += offset
        name_positions[station] = (x, y)
        if station in transfer_stations:
            canvas.create_text(x, y-15, text=station, fill='black', tags="station_name")
        else:
            station_color = station_colors.get(station, 'black') if station not in highlighted_stations else colors.get(sheet_name, 'black')
            canvas.create_text(x, y-15, text=station, fill=station_color, tags="station_name")


# 공통 focus_in 함수
def entry_focus_in(entry, listbox):
    entry.bind("<KeyRelease>", lambda event: key_release_handler(event, entry, listbox))
    
    entry.bind("<KeyPress-Up>", lambda event: move_up_listbox(listbox, entry))
    entry.bind("<KeyPress-Down>", lambda event: move_down_listbox(listbox, entry))
    entry.bind("<Return>", lambda event: select_from_listbox(entry, listbox))

    # FocusOut 시 리스트박스를 숨김
    entry.bind("<FocusOut>", lambda event: listbox.place_forget())

# IME에서 조합 중인 문자열을 가져오는 함수
def get_ime_composition_string(hwnd):
    hIMC = imm32.ImmGetContext(hwnd)
    if not hIMC:
        return None
    buffer_size = imm32.ImmGetCompositionStringW(hIMC, 8, None, 0)
    if buffer_size > 0:
        buffer = ctypes.create_unicode_buffer(buffer_size // 2)
        imm32.ImmGetCompositionStringW(hIMC, 8, buffer, buffer_size)
        return buffer.value
    return None

def key_release_handler(event, entry, listbox):
    input_text = entry.get()

    if event.keysym == "BackSpace" and len(input_text) == 0:
        listbox.place_forget()
        return
    
    if len(input_text) == 0: 
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        composition = get_ime_composition_string(hwnd)
        if composition:
            if re.fullmatch(r'[가-힣0-9]+', composition) and event.keysym not in ("Up", "Down", "Return"):
                update_autocomplete_list(entry, listbox, station_list, composition)
                adjust_listbox_size(entry, listbox)
            else:
                return
    else:
        if event.keysym not in ("Up", "Down", "Return"):
            update_autocomplete_list(entry, listbox, station_list, input_text)

def update_autocomplete_list(entry, listbox, station_list, search_text):
    input_text = search_text.lower()
    listbox.delete(0, tk.END)

    if input_text:
        starts_with = [station for station in station_list if station.lower().startswith(input_text)]
        starts_with.sort(reverse=True)

        contains = [station for station in station_list if input_text in station.lower() and not station.lower().startswith(input_text)]
        contains.sort(reverse=True)

        matching_stations = starts_with + contains

        if matching_stations:
            for station in matching_stations:
                listbox.insert(tk.END, station)

            # 리스트박스의 높이를 아이템 개수에 맞게 설정
            max_height = 50
            listbox_height = min(len(matching_stations), max_height)
            listbox.config(height=listbox_height)

            adjust_listbox_size(entry, listbox)
            listbox.select_set(0)
        else:
            listbox.place_forget()
    else:
        listbox.place_forget()

def move_up_listbox(listbox, entry):
    current_selection = listbox.curselection()
    if current_selection:
        index = current_selection[0]
        if index > 0:
            listbox.select_clear(index)
            listbox.select_set(index - 1)
            listbox.activate(index - 1)
    adjust_listbox_size(entry, listbox)

def move_down_listbox(listbox, entry):
    current_selection = listbox.curselection()
    if current_selection:
        index = current_selection[0]
        if index < listbox.size() - 1:
            listbox.select_clear(index)
            listbox.select_set(index + 1)
            listbox.activate(index + 1)
    adjust_listbox_size(entry, listbox)

def adjust_listbox_size(entry, listbox):
    listbox_height = min(listbox.size(), 10)
    listbox.config(height=listbox_height)
    listbox.place(x=entry.winfo_x(), y=entry.winfo_y()+ listbox.winfo_height() )
    listbox.lift()  # 리스트박스를 최상단으로 올리기

# 리스트박스 항목을 선택한 후 리스트박스를 숨김
def select_from_listbox(entry, listbox):
    if listbox.size() > 0:
        selected_station = listbox.get(tk.ACTIVE)
        entry.delete(0, tk.END)
        entry.insert(0, selected_station)
        listbox.place_forget()

# 마우스 클릭 시 리스트박스 항목을 선택한 후 리스트박스 숨김
def handle_click(event, entry, listbox):
    index = listbox.nearest(event.y)  # 마우스 클릭 위치의 항목 찾기
    listbox.select_clear(0, tk.END)
    listbox.select_set(index)
    listbox.activate(index)
    select_from_listbox(entry, listbox)

# 마우스가 움직일 때 선택 항목을 바꿈
def update_selection_on_mouse_move(event, listbox):
    index = event.widget.nearest(event.y)
    listbox.select_clear(0, tk.END)  # 기존 선택된 항목 클리어
    listbox.select_set(index)  # 마우스가 가리키는 항목 선택
    listbox.activate(index)

# 최단 경로 찾기 (다익스트라 알고리즘)
def visitPlace(visit, routing):
    routing[visit]['visited'] = 1
    for togo, betweenDist in landscape[visit].items():
        toDist = routing[visit]['shortestDist'] + betweenDist
        if routing[togo]['shortestDist'] > toDist:
            routing[togo]['shortestDist'] = toDist
            routing[togo]['route'] = copy.deepcopy(routing[visit]['route'])
            routing[togo]['route'].append(visit)

def find_shortest_path(start, end):
    routing = {}
    for place in landscape.keys():
        routing[place] = {'shortestDist': float('inf'), 'route': [], 'visited': 0}

    routing[start]['shortestDist'] = 0
    visitPlace(start, routing)

    while True:
        minDist = float('inf')
        toVisit = ''
        for name, search in routing.items():
            if 0 < search['shortestDist'] < minDist and not search['visited']:
                minDist = search['shortestDist']
                toVisit = name
        if toVisit == '':
            break
        visitPlace(toVisit, routing)

    return routing[end]['route'] + [end], routing[end]['shortestDist']

def clear_canvas():
    canvas.delete("facility")  # 태그가 "facility"인 아이콘만 삭제
    canvas.delete("line")  # 모든 노선 삭제
    canvas.delete("path")
    canvas.delete("station")  # 모든 역 삭제
    canvas.delete("station_name")  # 모든 역 삭제
    canvas.delete("station_oval")  # 모든 역 삭제
    canvas.delete("icon")

# 경로 그리기
def draw_shortest_path(start, end):
    clear_canvas()
    path, distance = find_shortest_path(start, end)
    if not path:
        return

    used_lines = set()
    # 경로 상의 노선만 사용하여 노선 리스트 작성
    for i in range(len(path) - 1):
        station1 = path[i]
        station2 = path[i + 1]
        for sheet_name, data in lines_df.items():
            for j in range(len(data) - 1):
                line_station1 = data.iloc[j]['지하철명']
                line_station2 = data.iloc[j + 1]['지하철명']
                if (line_station1 == station1 and line_station2 == station2) or (line_station1 == station2 and line_station2 == station1):
                    used_lines.add(sheet_name)
                    break

    # 경로 상의 노선만 다시 그리기
    for sheet_name, color in colors.items():
        if sheet_name in used_lines:  # 경로에 포함된 노선만 그리기
            data = lines_df[sheet_name]
            for i in range(len(data) - 1):
                station1 = data.iloc[i]['지하철명']
                station2 = data.iloc[i + 1]['지하철명']
                if (station1 in path and station2 in path) or (station1 in path and station2 in path):
                    x1, y1 = data.iloc[i]['X'], data.iloc[i]['Y']
                    x2, y2 = data.iloc[i + 1]['X'], data.iloc[i + 1]['Y']
                    canvas.create_line(x1, y1, x2, y2, fill=color, width=4, tags="path")

    # 경로 상의 역만 다시 표시
    for station in path:
        x, y = station_positions[station]
        
        if station in transfer_stations:
            if station == '부전':
                canvas.create_image(x+10, y, image=transfer_image_bu, anchor=tk.CENTER, tags="station")
            elif station == '벡스코(시립미술관)':
                canvas.create_image(x, y+10, image=transfer_image_bex, anchor=tk.CENTER, tags="station")
            else:
                canvas.create_image(x, y, image=transfer_image, anchor=tk.CENTER, tags="station")
        else:
            canvas.create_oval(x-5, y-5, x+5, y+5, fill='red', tags="station")
        
        canvas.create_text(x, y-15, text=station, fill='red', tags="station")
    
    # 경로 상의 아이콘 다시 추가
    for station in path:
        x, y = station_positions[station]
        
        if station == start:
            add_image(x-s_x_offset, y-y_offset, start_image)
        elif station == end:
            add_image(x-x_offset, y-y_offset, end_image)

    # 거리와 시간 계산
    total_distance = 0  # 총 거리 (Km)
    total_time = 0  # 총 시간 (분)
    prev_line = None
    segment_distances = []

    for i in range(len(path) - 1):
        station1 = path[i]
        station2 = path[i + 1]
        line1 = line_mapping[station1].intersection(line_mapping[station2]).pop()

        if prev_line is None or prev_line == line1:
            # 동일 노선 이동: 2km, 2분씩 증가
            segment_distances.append(2)
            total_distance += 2
            total_time += 2
        else:
            # 환승: 4km, 4분 추가
            segment_distances.append(6)  # 기본 2km 이동 + 4km 환승 거리
            total_distance += 6  # 기본 2km 이동 + 4km 환승 거리
            total_time += 6  # 기본 2분 이동 + 4분 환승 시간

        prev_line = line1

    # 총 이동 거리 및 시간 출력
    print(f"총 이동 거리: {total_distance} km")
    print(f"총 이동 시간: {total_time} 분")

    # UI에 시간 정보 업데이트
    time_label.config(text=f"총 여행 시간: {total_time} 분, 총 이동 거리: {total_distance} km")

    # 경로 세부정보 업데이트
    update_details(path, {
        'total_distance': total_distance,
        'total_time': total_time,
        'segment_distances': segment_distances
    })

# 경로 세부정보 업데이트 함수
def update_details(path, distances):
    details_text.delete(1.0, tk.END)  # 기존 텍스트 삭제

    # 경로 세부정보 텍스트 생성
    details = "최단 경로: {}\n".format(" -> ".join(path))
    details += "총 이동 거리: {} km\n".format(distances['total_distance'])
    details += "총 여행 시간: {} 분\n".format(distances['total_time'])

    details_text.insert(tk.END, details)
    
    
# 체크박스 상태를 저장할 변수들
facility_vars = {
    '엘레베이터': IntVar(),
    '휠체어리프트': IntVar(),
    '환승주차장': IntVar(),
    '자전거보관소': IntVar(),
    '물품보관함': IntVar(),
    '자동사진기': IntVar(),
    '도시철도경찰대': IntVar(),
    '섬식형': IntVar(),
    '반대방향': IntVar()
}

# 시트에서 역 정보 읽기
stations = []
for sheet_name, data in sheets.items():
    if '지하철명' in data.columns and 'X' in data.columns and 'Y' in data.columns:
        for index, row in data.iterrows():
            station_info = {
                'name': row['지하철명'],
                'x': row['X'],
                'y': row['Y'],
                'facilities': {
                    '엘레베이터': row.get('엘레베이터', 0),
                    '휠체어리프트': row.get('휠체어리프트', 0),
                    '환승주차장': row.get('환승주차장', 0),
                    '자전거보관소': row.get('자전거보관소', 0),
                    '물품보관함': row.get('물품보관함', 0),
                    '자동사진기': row.get('자동사진기', 0),
                    '도시철도경찰대': row.get('도시철도경찰대', 0),
                    '섬식형': row.get('섬식형', 0),
                    '반대방향': row.get('반대방향', 0),
                }
            }
            stations.append(station_info)

def show_line(line_name):
    clear_canvas()  # 기존 노선 및 역 삭제
    
    if line_name:
        data = lines_df[line_name]
        color = colors[line_name]
        
        # 선택된 노선의 라인만 그리기
        for i in range(len(data) - 1):
            station1 = data.iloc[i]['지하철명']
            station2 = data.iloc[i + 1]['지하철명']
            x1, y1 = data.iloc[i]['X'], data.iloc[i]['Y']
            x2, y2 = data.iloc[i + 1]['X'], data.iloc[i + 1]['Y']
            canvas.create_line(x1, y1, x2, y2, fill=color, width=4, smooth=True, tags="line")

        
        # 환승역을 세트로 만듭니다.
        transfer_stations = set(transfer_df['지하철명'].unique())
            # 역을 표시한 세트를 만듭니다.
        displayed_stations = set()
        
        # 선택된 노선의 역만 그리기
        for index, row in data.iterrows():
            x, y = row['X'], row['Y']
            name = row['지하철명']
            if name in transfer_stations:
                if name not in displayed_stations:
                    canvas.create_image(x, y, image=transfer_image, anchor=tk.CENTER, tags="station")
                    displayed_stations.add(name)
            else:
                station_color = station_colors.get(name, 'black')
                canvas.create_oval(x-5, y-5, x+5, y+5, fill=station_color, tags="station")
            canvas.create_text(x, y-15, text=name, fill=color, tags="station_name")
    else:
        draw_map()  # 선택된 노선이 없으면 모든 노선 그리기
        
def create_line_buttons():
    # 각 노선별 버튼 생성
    for line_name in colors.keys():
        if line_name != '환승역':  # 환승역을 제외하고 버튼 생성
            color = colors[line_name]
            button = tk.Button(line_buttons_frame, bg=color, text=line_name, command=lambda ln=line_name: show_line(ln))
            button.pack(side=tk.LEFT, padx=2, pady=2)
    
    # "전체 역 보기" 버튼 추가
    show_all_button = tk.Button(line_buttons_frame, text="전체 역 보기", command=draw_map)
    show_all_button.pack(side=tk.LEFT, padx=5, pady=2)
    
def create_facility_buttons():
    """
    편의시설 버튼을 생성하고 프레임에 추가합니다.
    """
    global facility_vars  # 전역 변수로 facility_vars를 사용
    facility_vars = {}  # facility_vars 초기화

    # 편의시설 버튼 생성
    for facility in ['엘레베이터', '휠체어리프트', '환승주차장', '자전거보관소', '물품보관함', '자동사진기', '도시철도경찰대', '섬식형', '반대방향']:
        var = tk.IntVar()  # 체크박스의 상태를 관리할 변수
        facility_vars[facility] = var
        button = tk.Button(category_btn_frame, text=facility, command=lambda f=facility: show_facilities(f))
        button.pack(side=tk.LEFT, padx=2, pady=2)   



def show_facilities(selected_facility=None):
    """
    선택된 편의시설을 화면에 표시합니다.
    """
    canvas.delete("facility")  # 태그가 "facility"인 아이콘만 삭제
    draw_map()
    for station in stations:
        x, y = station['x'], station['y']
        # 모든 시설 표시 또는 선택된 시설이 있는 경우만 표시
        if selected_facility is None:
            for facility in facility_vars.keys():
                if station['facilities'].get(facility, 0) == 1:
                    # 모든 시설 아이콘을 표시
                    canvas.create_image(x, y-15, image=here_image, anchor=tk.CENTER, tags="facility")
                    break
        else:
            if station['facilities'].get(selected_facility, 0) == 1:
                # 선택된 시설 아이콘을 표시
                    canvas.create_image(x, y-15, image=here_image, anchor=tk.CENTER, tags="facility")


canvas.bind("<Button-1>", on_click)
create_facility_buttons()  # 편의시설 버튼 생성
create_line_buttons()
draw_map()
root.mainloop()