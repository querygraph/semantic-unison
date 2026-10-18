exception Creation_failed
let mode=ref "known"
let after_adopt read write =
 PipeFault.read_fd:=read;PipeFault.write_fd:=write;
 PipeFault.fail_read:=(!mode="read" || !mode="both" || !mode="creation-raw" || !mode="creation-wrapped");
 PipeFault.fail_write:=(!mode="write" || !mode="both" || !mode="creation-raw" || !mode="creation-wrapped");
 if !mode="creation-raw" then raise Creation_failed
let before_wrapper ()=if !mode="creation-wrapped" then raise Creation_failed
