//! Read-only nested DNG interpretation. No writer, paths from peer, or exclusions.
use exiftool_rs::{ExifTool, Options, Value};
use std::io::Read;
use std::path::Path;
const MAX_INPUT: u64 = 256 * 1024 * 1024;
fn quote(s: &str) -> String {
    let mut out=String::from("\"");
    for c in s.chars() { match c {
        '"'=>out.push_str("\\\""), '\\'=>out.push_str("\\\\"),
        c if c<' '=>out.push_str(&format!("\\u{:04x}",c as u32)), c=>out.push(c)
    }} out.push('"');out
}
fn value(v: &Value, depth: usize) -> Result<String,String> {
    if depth>16 {return Err("value depth limit".into())}
    let (kind,body)=match v {
        Value::String(s)=>("string",quote(s)),
        Value::U8(v)=>("u8",v.to_string()), Value::U16(v)=>("u16",v.to_string()),
        Value::U32(v)=>("u32",v.to_string()), Value::I16(v)=>("i16",v.to_string()),
        Value::I32(v)=>("i32",v.to_string()),
        Value::URational(a,b)=>("urational",format!("[{a},{b}]")),
        Value::IRational(a,b)=>("irational",format!("[{a},{b}]")),
        Value::F32(v)=>("f32_bits",quote(&format!("{:08x}",v.to_bits()))),
        Value::F64(v)=>("f64_bits",quote(&format!("{:016x}",v.to_bits()))),
        Value::Binary(b)|Value::Undefined(b)=>{
            if b.len()>65536 {return Err("binary field limit".into())}
            let hex:String=b.iter().map(|x|format!("{x:02x}")).collect();
            (if matches!(v,Value::Binary(_)){"binary_hex"}else{"undefined_hex"},quote(&hex))
        },
        Value::List(items)=>{
            if items.len()>4096{return Err("list limit".into())}
            let vals=items.iter().map(|v|value(v,depth+1)).collect::<Result<Vec<_>,_>>()?;
            ("list",format!("[{}]",vals.join(",")))
        },
        Value::Struct(fields)=>{
            if fields.len()>4096{return Err("struct limit".into())}
            let vals=fields.iter().map(|(k,v)|Ok(format!("[{},{}]",quote(k),value(v,depth+1)?))).collect::<Result<Vec<_>,String>>()?;
            ("struct",format!("[{}]",vals.join(",")))
        }
    };
    let result=format!("[{},{}]",quote(kind),body);
    if result.len()>262144{return Err("field encoding limit".into())} Ok(result)
}
fn run() -> Result<(),String> {
    let args:Vec<_>=std::env::args().collect();
    if args.len()!=3 || args[1]!="--fd" {return Err("requires --fd N".into())}
    let fd:u32=args[2].parse().map_err(|_|"invalid fd")?;
    if fd<3{return Err("explicit inherited source descriptor required".into())}
    let file=std::fs::File::open(format!("/dev/fd/{fd}")).map_err(|e|e.to_string())?;
    let info=file.metadata().map_err(|e|e.to_string())?;
    if !info.is_file() || info.len()>MAX_INPUT{return Err("regular input <=256MiB required".into())}
    let mut data=Vec::new();file.take(MAX_INPUT+1).read_to_end(&mut data).map_err(|e|e.to_string())?;
    if data.len() as u64!=info.len(){return Err("input changed or exceeded limit".into())}
    let engine=ExifTool::with_options(Options{duplicates:true,print_conv:false,show_unknown:2,struct_output:true,..Options::default()});
    let tags=engine.extract_info_from_bytes(&data,Path::new("/__unison_metadata_only__/input.dng")).map_err(|e|e.to_string())?;
    let mut records=Vec::new();let mut warnings=Vec::new();
    for tag in tags {
        if tag.group.family0=="ExifTool" && (tag.name=="Warning" || tag.name=="Error") {
            warnings.push(quote(&tag.raw_value.to_display_string()));
        }
        if tag.group.family0!="MakerNotes" {continue}
        if records.len()>=4096{return Err("MakerNote tag count limit".into())}
        records.push(format!("{{\"group\":{},\"document\":{},\"name\":{},\"id\":{},\"value\":{}}}",
            quote(&tag.group.family1),quote(&tag.group.family3),quote(&tag.name),
            quote(&format!("{:?}",tag.id)),value(&tag.raw_value,0)?));
    }
    let output=format!("{{\"schema\":\"unison-exiftool-rs-values/1\",\"engine_version\":{},\"exiftool_version\":{},\"maker_notes\":[{}],\"warnings\":[{}]}}",
        quote(exiftool_rs::VERSION),quote(exiftool_rs::EXIFTOOL_VERSION),records.join(","),warnings.join(","));
    if output.len()>240000{return Err("observation output limit".into())}
    println!("{output}");Ok(())
}
fn main(){if let Err(e)=run(){eprintln!("{e}");std::process::exit(2)}}
