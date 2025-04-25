print("✅ BehaviorAgent Server 已启动！")


import carla
import time
import os
import sys

sys.path.append("D:/CARLA/CARLA_0.9.15/WindowsNoEditor/PythonAPI")
sys.path.append("D:/CARLA/CARLA_0.9.15/WindowsNoEditor/PythonAPI/agents")

from agents.navigation.behavior_agent import BehaviorAgent

client = carla.Client("localhost", 2000)
client.set_timeout(60.0)
world = client.get_world()
map = world.get_map()

print("Waiting for vehicle...")
vehicle = None
while vehicle is None:
    vehicles = world.get_actors().filter("vehicle.*")
    if len(vehicles) > 0:
        vehicle = vehicles[0]
    else:
        time.sleep(0.5)

print(f"✅ Vehicle found: {vehicle.type_id}")
agent = BehaviorAgent(vehicle, behavior="normal")

print("✅ BehaviorAgent running...")

while True:
    if os.path.exists("control.txt"):
        with open("control.txt", "r") as f:
            cmd = f.read().strip().lower()

        if cmd == "change_lane_left":
            wp = map.get_waypoint(vehicle.get_location())
            print(
                f"[INFO] 当前 waypoint: lane_id={wp.lane_id}, 变道权限={wp.lane_change}"
            )

            wp_left = wp.get_left_lane()

            if wp_left:
                print(f"[INFO] 左侧 lane_id: {wp_left.lane_id}")
                # 获取左侧前方 30 米的 waypoint
                target = wp_left.next(30.0)[0]

                # 再获取它前方 80 米（确保足够导航）
                final = target.next(80.0)[0]

                agent.set_destination(final.transform.location)
                print(f"[INFO] 设置目标为左车道远方: {final.transform.location}")

                # ✅ 等待规划成功
                while len(agent._local_planner._waypoints_queue) == 0:

                    print("[INFO] 等待路径规划完成...")

                    time.sleep(0.1)

                    agent._update_information()
                    print("[✅] 规划完成，开始变道")
            else:
                print("❌ 当前无左侧车道，变道失败")

        os.remove("control.txt")

    agent._update_information()

    try:
        if agent.done():
            print("🅿️ 变道完成并已到达目标，自动停车")
            control = carla.VehicleControl(throttle=0.0, brake=1.0)
            vehicle.apply_control(control)
            break  # 退出循环
        control = agent.run_step()
        vehicle.apply_control(control)
    except AttributeError as e:
        print(f"[ERROR] run_step() 出错：{e}")
        continue

    world.tick()
    time.sleep(0.05)
