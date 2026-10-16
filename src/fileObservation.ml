type t = {
  device_id : string;
  file_id : string;
  kind : Unix.file_kind;
  size : int64;
  link_count : int64;
  file_flags : int64;
  filesystem_id : string;
  mount_flags : int64;
  volume_uuid : string option;
  mtime_seconds : int64;
  mtime_nanoseconds : int;
  ctime_seconds : int64;
  ctime_nanoseconds : int;
}

external observe : Unix.file_descr -> t = "unison_file_observation"
