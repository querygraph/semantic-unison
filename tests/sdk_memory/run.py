#!/usr/bin/env python3
"""Source compilation with actual SDK headers; execute original/mocked code only."""
import argparse,pathlib,tempfile,subprocess,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('--sdk-root',type=pathlib.Path,required=True);p.add_argument('--dependency-build-dir',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parents[2];w=pathlib.Path(tempfile.mkdtemp(prefix='unison-sdk-memory-')).resolve();adapter=r/'tools/adobe-validator';sdk=a.sdk_root.resolve();dep=a.dependency_build_dir.resolve();records=[]
H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
sources=[adapter/n for n in ['memory_budget.h','memory_allocator.h','area_task_host.h','area_scheduler.h','driver.cpp','build.py']]+[pathlib.Path(__file__),pathlib.Path(__file__).with_name('test.cpp'),pathlib.Path(__file__).with_name('mock_sdk.h')];pins={str(p.relative_to(r)):H(p) for p in sources}
for f in sources:shutil.copyfile(f,w/f.name)
(w/'dng_memory.h').write_text('#include "mock_sdk.h"\n');(w/'dng_exceptions.h').write_text('#include "mock_sdk.h"\n')
def run(args,name,code=0):
 x=subprocess.run(list(map(str,args)),cwd=w,capture_output=True,text=True,timeout=60);log=w/(name+'.log');log.write_text(x.stdout+x.stderr);records.append(dict(name=name,args=list(map(str,args)),exit=x.returncode,expectedExit=code,log=str(log),logSha256=H(log)));assert x.returncode==code,(name,x.stdout,x.stderr);return x.stdout+x.stderr
sdk_sources=[sdk/'DNG_ReadMe.txt']+[sdk/'dng_sdk/source'/n for n in ['dng_memory.h','dng_memory.cpp','dng_host.h','dng_host.cpp','dng_jxl.cpp','dng_area_task.h','dng_flags.h','dng_types.h','dng_exceptions.h','dng_safe_arithmetic.h']]
sdk_pins={str(f):H(f) for f in sdk_sources}
j=dict(schema='unison-sdk-memory-source/1',work=str(w),records=records,sdkRuntimeQualified=False,productionEnabled=False,processRssBounded=False)
try:
 assert '1.7.1 2724' in (sdk/'DNG_ReadMe.txt').read_text()
 compile((adapter/'build.py').read_text(),str(adapter/'build.py'),'exec')
 for mode,extra in [('scalar',[]),('avx',['-DMOCK_AVX=1']),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
  run(['clang++','-std=c++17','-pthread','-Wall','-Wextra','-Werror','-O1',*extra,'-I',w,w/'test.cpp','-o',w/mode],mode+'-compile');print(run([w/mode],mode+'-run'),end='')
 neg=w/'negative';neg.mkdir();original=(w/'memory_budget.h').read_text();needle='if(bytes>limit_-used_)';assert original.count(needle)==1;(neg/'memory_budget.h').write_text(original.replace(needle,'if(false && bytes>limit_-used_)'))
 for n in ['memory_allocator.h','mock_sdk.h','dng_memory.h','dng_exceptions.h']:shutil.copyfile(w/n,neg/n)
 shutil.copyfile(w/'test.cpp',neg/'test.cpp');run(['clang++','-std=c++17','-pthread','-O1','-I',neg,neg/'test.cpp','-o',neg/'test'],'negative-private-compile');text=run([neg/'test'],'negative-run',1);assert 'exhausted zero-byte allocation declined' in text
 failure=w/'malloc-failure';failure.mkdir();needle='void *raw=std::malloc(charged);';assert original.count(needle)==1;(failure/'memory_budget.h').write_text(original.replace(needle,'void *raw=nullptr;'))
 (failure/'test.cpp').write_text('#include "memory_budget.h"\nint main(){unison_memory::Budget b(512);for(int i=0;i<1000;i++){if(b.try_malloc(100)!=nullptr)return 1;auto u=b.usage();if(u.used||u.live||u.peak!=100+b.overhead())return 2;}return 0;}\n')
 run(['clang++','-std=c++17','-pthread','-O1','-I',failure,failure/'test.cpp','-o',failure/'test'],'malloc-failure-compile');run([failure/'test'],'malloc-failure-run')
 xmp=sdk/'xmp/toolkit';inc=[sdk/'dng_sdk/source',sdk/'libjpeg',xmp,xmp/'public/include',xmp/'third-party/expat/public/lib',xmp/'XMPCore/resource/mac',sdk/'libjxl/libjxl/lib/include',dep/'jxl/lib/include',sdk/'libjxl/client_projects/include']
 flags=['-O1','-std=c++17','-DNDEBUG=1','-DMAC_ENV=1','-DXMP_StaticBuild=1','-DXMP_64=1','-DENABLE_CPP_DOM_MODEL=0','-DXML_STATIC=1','-DHAVE_EXPAT_CONFIG_H=1','-DqDNGValidate=1','-DqDNGValidateTarget=1','-DqDNGReportErrors=1','-DqDNGXMPFiles=0','-DqDNGXMPDocOps=0','-DqDNGUseLibJPEG=1','-DqMacOS=1','-DqWinOS=0','-DqDNGUseStdInt=1','-DMacintosh=1','-funsigned-char','-fno-common','-Wall','-Wextra']+[str(x) for path in inc for x in ['-I',path]]
 # Do not use mock include directory for genuine SDK compilations.
 for mode,extra in [('single',[]),('area',['-DUNISON_EXPERIMENTAL_AREA_TASK_HOST=1']),('memory',['-DUNISON_EXPERIMENTAL_MEMORY_BUDGET=1']),('area-memory',['-DUNISON_EXPERIMENTAL_MEMORY_BUDGET=1','-DUNISON_EXPERIMENTAL_AREA_TASK_HOST=1'])]:
  run(['clang++',*flags,*extra,'-c',adapter/'driver.cpp','-o',w/('driver-'+mode+'.o')],'sdk-headers-'+mode)
 for f,h in pins.items():assert H(r/f)==h,('source drift',f)
 for f,h in sdk_pins.items():assert H(f)==h,('SDK source drift',f)
 j.update(status='passed',sourcePins=pins,sdkInputs=sdk_pins,scope='Original quota + independent SDK-interface surrogate runtime; real SDK-header compilation only. No SDK linking/initialization, codec, Photo, Lightroom or benchmark.')
finally:
 j.setdefault('status','failed');a.receipt.write_text(json.dumps(j,indent=2)+'\n');(w/'RESULT.json').write_text(json.dumps(j,indent=2)+'\n')
