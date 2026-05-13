from jarvis.automation.linux import run_cmd, get_system_info, get_current_time, get_current_date, shutdown, reboot
from jarvis.automation.apps import launch_app, open_project_folder, check_docker
from jarvis.automation.media import volume_up, volume_down, volume_set, volume_mute, volume_get
from jarvis.automation.terminal import execute_command, open_terminal

from jarvis.automation.services import (
    service_status, service_start, service_stop, service_restart,
    service_enable, service_disable, list_services, is_systemctl_available,
)
from jarvis.automation.network import (
    wifi_status, wifi_connect, wifi_disconnect, wifi_scan,
    network_status, is_nmcli_available,
)
from jarvis.automation.bluetooth import (
    bluetooth_status, bluetooth_on, bluetooth_off, bluetooth_scan,
    bluetooth_pair, bluetooth_connect, bluetooth_disconnect,
    bluetooth_devices, is_bluetoothctl_available,
)
from jarvis.automation.window_manager import (
    get_workspaces, switch_workspace, get_windows, get_wm_info,
    move_window, resize_window,
)
from jarvis.automation.docker_tools import (
    docker_status, docker_ps, docker_compose_up, docker_compose_down,
    docker_images, docker_pull, docker_stop, docker_logs, is_docker_available,
)
from jarvis.automation.git_tools import (
    git_run, git_status, git_log, git_branch, git_diff,
    git_commit, git_push, git_pull, git_stash, git_pop, is_git_available,
)
from jarvis.automation.tmux_tools import (
    tmux_list_sessions, tmux_new_session, tmux_kill_session,
    tmux_send_command, tmux_list_windows, is_tmux_available,
)
