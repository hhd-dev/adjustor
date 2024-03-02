import logging
import os
from threading import Event as TEvent, Thread
from typing import Sequence

from hhd.plugins import Context, HHDPlugin, HHDSettings, load_relative_yaml
from hhd.plugins.conf import Config
from hhd.plugins.plugin import Emitter

from adjustor.core.acpi import check_perms, initialize
from adjustor.core.const import CPU_DATA, DEV_DATA, ROG_ALLY_PP_MAP

from .utils import exists_sentinel, install_sentinel, remove_sentinel

logger = logging.getLogger(__name__)


class AdjustorInitPlugin(HHDPlugin):
    def __init__(self) -> None:
        self.name = f"adjustor_init"
        self.priority = 5
        self.log = "adji"
        self.init = False
        self.failed = False
        self.safe_mode = False

    def open(self, emit: Emitter, context: Context):
        if exists_sentinel() or not install_sentinel():
            self.safe_mode = True

    def settings(self):
        return {}

    def update(self, conf: Config):
        if self.failed:
            conf["hhd.settings.tdp_enable"] = False
        if self.safe_mode:
            logger.warning(f"Due to a sentinel error, auto-start is disabled.")
            conf["hhd.settings.tdp_error"] = (
                "Due to Handheld Daemon not exiting properly, auto-start is disabled."
            )
            conf["hhd.settings.tdp_enable"] = False
            self.safe_mode = False

        if self.init:
            return

        if not conf["hhd.settings.tdp_enable"].to(bool):
            return

        initialize()
        if not check_perms():
            conf["hhd.settings.tdp_enable"] = False
            conf["hhd.settings.tdp_error"] = (
                "Can not write to 'acpi_call'. It is required for TDP."
            )
            self.failed = True

        self.init = True

    def close(self):
        remove_sentinel()


class AdjustorPlugin(HHDPlugin):
    def __init__(self) -> None:
        self.name = f"adjustor_main"
        self.priority = 80
        self.log = "adjs"
        self.enabled = False
        self.enfoce_limits = True

        self.t = None
        self.should_exit = None

    def settings(self) -> HHDSettings:
        out = {"hhd": {"settings": load_relative_yaml("settings.yml")}}
        if os.environ.get("HHD_ADJ_ENABLE_TDP"):
            out["hhd"]["settings"]["children"]["tdp_enable"]["default"] = True
        return out

    def _start(self):
        if self.should_exit or self.t:
            return
        try:
            from .events import loop_process_events

            self.should_exit = TEvent()
            self.t = Thread(
                target=loop_process_events, args=(self.emit, self.should_exit)
            )
            self.t.start()
        except Exception as e:
            logger.warning(
                f"Could not init ACPI event handling. Is pyroute2 installed?"
            )

    def _stop(self):
        if not self.should_exit or not self.t:
            return
        self.should_exit.set()
        self.t.join()
        self.should_exit = None
        self.t = None

    def open(
        self,
        emit,
        context: Context,
    ):
        self.emit = emit

    def update(self, conf: Config):
        new_enabled = conf["hhd.settings.tdp_enable"].to(bool)
        new_enforce_limits = conf["hhd.settings.enforce_limits"].to(bool)
        if new_enabled != self.enabled or new_enforce_limits != self.enfoce_limits:
            self.emit({"type": "settings"})
        self.enabled = new_enabled
        self.enfoce_limits = new_enforce_limits

        if self.enabled:
            self._start()
        else:
            self._stop()

    def close(self):
        self._stop()


def autodetect(existing: Sequence[HHDPlugin]) -> Sequence[HHDPlugin]:
    if len(existing):
        return existing

    from .drivers.lenovo import LenovoDriverPlugin
    from .drivers.smu import SmuDriverPlugin, SmuQamPlugin

    drivers = []
    with open("/sys/devices/virtual/dmi/id/product_name") as f:
        prod = f.read().strip()
    with open("/proc/cpuinfo") as f:
        cpuinfo = f.read().strip()

    drivers_matched = False
    if prod == "83E1":
        drivers.append(LenovoDriverPlugin())
        drivers_matched = True

    if os.environ.get("HHD_ADJ_DEBUG") or os.environ.get("HHD_ENABLE_SMU"):
        drivers_matched = False

    if not drivers_matched and prod in DEV_DATA:
        dev, cpu, pp_enable = DEV_DATA[prod]
        pp_enable |= bool(os.environ.get("HHD_ADJ_DEBUG"))
        drivers.append(
            SmuDriverPlugin(
                dev,
                cpu,
                platform_profile=pp_enable,
            )
        )
        drivers.append(
            SmuQamPlugin(
                dev, ROG_ALLY_PP_MAP if pp_enable else None, init_tdp=not prod == "83E1"
            ),
        )
        drivers_matched = True

    if not drivers_matched:
        for name, (dev, cpu) in CPU_DATA.items():
            if name in cpuinfo:
                drivers.append(
                    SmuDriverPlugin(
                        dev,
                        cpu,
                        platform_profile=True,
                    )
                )
                drivers.append(
                    SmuQamPlugin(dev, ROG_ALLY_PP_MAP),
                )
                break

    if not drivers:
        logger.info(f"No tdp drivers found for this device, exiting Adjustor.")
        return []

    return [
        *drivers,
        AdjustorInitPlugin(),
        AdjustorPlugin(),
    ]
