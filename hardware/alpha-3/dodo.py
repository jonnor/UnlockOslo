from ee.bom.doit import *
from ee.digikey.doit import *
from ee.doit import configure_logging
from ee.ds import DataSetManager
from ee.kicad.doit import *


def configure_kicad():
    from ee.kicad.doit import doit_config, init
    doit_config.configure(data_set_manager=dsm)
    doit_config.append_in_data_set_for_task(task_kicad_create_component_data_set, kicad_footprint)
    init(sch=sch, kicad_pcb=kicad_pcb, gerber_dir="gerber", )


def configure_bom():
    from ee.bom.doit import doit_config
    doit_config.configure(data_set_manager=dsm)


def configure_digikey():
    from ee.digikey.doit import doit_config
    doit_config.configure(data_set_manager=dsm)


# Configure DoIt
configure_logging()

DOIT_CONFIG = {'check_file_uptodate': 'timestamp'}

prj = "alpha"
sch = "{}.sch".format(prj)
kicad_pcb = "{}.kicad_pcb".format(prj)

dsm = DataSetManager("ee")

kicad_footprint = "kicad-footprint"
dsm.register_ds("csv", kicad_footprint, "kicad-footprint-mapping", path="ee/kicad-footprint.csv")

configure_kicad()
configure_bom()
configure_digikey()


def task_orders():
    import ee.bom.doit
    import ee.digikey.doit

    bom_cfg = ee.bom.doit.doit_config
    digikey_cfg = ee.digikey.doit.doit_config

    data_sets = [bom_cfg.out_data_set_for(task_bom),
                 digikey_cfg.out_data_set_for(task_digikey_resolve_schematic_components)]

    yield create_task_order_csv(
        output_file="ee/order.csv",
        out_data_set="order",
        data_sets=data_sets)

    for size in [1, 100]:
        yield create_task_order_csv(
            output_file="ee/digikey-{}.csv".format(size) if size != 1 else "ee/digikey.csv",
            style="digikey",
            out_data_set="digikey-order-{}".format(size),
            data_sets=data_sets,
            count=size)
