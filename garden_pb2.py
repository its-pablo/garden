# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: garden.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'garden.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import duration_pb2 as google_dot_protobuf_dot_duration__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0cgarden.proto\x12\x06garden\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1egoogle/protobuf/duration.proto\"\xf5\x08\n\tcontainer\x12\x13\n\theartbeat\x18\x01 \x01(\x05H\x00\x12>\n\x12\x61ll_device_updates\x18\x02 \x01(\x0b\x32 .garden.container.device_updatesH\x00\x12\x1c\n\x12get_device_updates\x18\x03 \x01(\x05H\x00\x12<\n\x11set_watering_time\x18\x04 \x01(\x0b\x32\x1f.garden.container.watering_timeH\x00\x12\x1c\n\x12get_watering_times\x18\x05 \x01(\x05H\x00\x12 \n\x16get_next_watering_time\x18\x06 \x01(\x05H\x00\x12\x34\n\twater_now\x18\x07 \x01(\x0b\x32\x1f.garden.container.watering_timeH\x00\x12\x17\n\rstop_watering\x18\x08 \x01(\x05H\x00\x12=\n\x12next_watering_time\x18\t \x01(\x0b\x32\x1f.garden.container.watering_timeH\x00\x12>\n\x12\x61ll_watering_times\x18\n \x01(\x0b\x32 .garden.container.watering_timesH\x00\x12?\n\x14\x63\x61ncel_watering_time\x18\x0b \x01(\x0b\x32\x1f.garden.container.watering_timeH\x00\x12*\n\x08pump_now\x18\x0c \x01(\x0b\x32\x16.garden.container.pumpH\x00\x12\x16\n\x0cstop_pumping\x18\r \x01(\x05H\x00\x1aJ\n\rdevice_update\x12)\n\x06\x64\x65vice\x18\x01 \x01(\x0e\x32\x19.garden.container.devices\x12\x0e\n\x06status\x18\x02 \x01(\x08\x1a\x42\n\x0e\x64\x65vice_updates\x12\x30\n\x07updates\x18\x01 \x03(\x0b\x32\x1f.garden.container.device_update\x1az\n\rwatering_time\x12-\n\ttimestamp\x18\x01 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12+\n\x08\x64uration\x18\x02 \x01(\x0b\x32\x19.google.protobuf.Duration\x12\r\n\x05\x64\x61ily\x18\x03 \x01(\x08\x1a@\n\x0ewatering_times\x12.\n\x05times\x18\x01 \x03(\x0b\x32\x1f.garden.container.watering_time\x1a\x33\n\x04pump\x12+\n\x08\x64uration\x18\x01 \x01(\x0b\x32\x19.google.protobuf.Duration\"\x94\x01\n\x07\x64\x65vices\x12\x0b\n\x07\x44\x45V_UNK\x10\x00\x12\x10\n\x0c\x44\x45V_ACT_PUMP\x10\x01\x12\x11\n\rDEV_ACT_VALVE\x10\x02\x12\x15\n\x11\x44\x45V_SNS_TANK_FULL\x10\x03\x12\x16\n\x12\x44\x45V_SNS_TANK_EMPTY\x10\x04\x12\x16\n\x12\x44\x45V_SNS_WELL_EMPTY\x10\x05\x12\x10\n\x0c\x44\x45V_SNS_RAIN\x10\x06\x42\n\n\x08\x63ontentsb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'garden_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CONTAINER']._serialized_start=90
  _globals['_CONTAINER']._serialized_end=1231
  _globals['_CONTAINER_DEVICE_UPDATE']._serialized_start=683
  _globals['_CONTAINER_DEVICE_UPDATE']._serialized_end=757
  _globals['_CONTAINER_DEVICE_UPDATES']._serialized_start=759
  _globals['_CONTAINER_DEVICE_UPDATES']._serialized_end=825
  _globals['_CONTAINER_WATERING_TIME']._serialized_start=827
  _globals['_CONTAINER_WATERING_TIME']._serialized_end=949
  _globals['_CONTAINER_WATERING_TIMES']._serialized_start=951
  _globals['_CONTAINER_WATERING_TIMES']._serialized_end=1015
  _globals['_CONTAINER_PUMP']._serialized_start=1017
  _globals['_CONTAINER_PUMP']._serialized_end=1068
  _globals['_CONTAINER_DEVICES']._serialized_start=1071
  _globals['_CONTAINER_DEVICES']._serialized_end=1219
# @@protoc_insertion_point(module_scope)
