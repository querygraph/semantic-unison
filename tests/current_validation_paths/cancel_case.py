"""Original cancellation assertions with retained source Session.cancel.

No Popen, killpg, bare open or numeric helper-liveness inference. Actual direct
client SIGINT and raw helper/client/server settlement are owned by the actor.
"""
def factory(session_type):
    def cancelled(root,binary,policy):
        session=session_type(root,binary);name='cancelled.dng'
        previous=b'previous live cancellation fixture\n'*128
        incoming=previous+b'reverse receive that must never commit after cancellation'
        # Assertion helpers remain original definitions in the legacy namespace.
        legacy=session_type.original_assertions
        verify_call=legacy['verify_call'];no_op=legacy['no_op'];equal=legacy['assert_equal']
        session.control(name);(session.left/name).write_bytes(previous);session.sync()
        (session.right/name).write_bytes(incoming);session.control(name,client='hang')
        before=len(session.calls('client'));log=session.cancel(name,incoming,previous,policy=policy)
        current=session.calls('client')
        if len(current)!=before+1:raise AssertionError('one cancelled receiving helper required')
        call=current[-1];verify_call(call,incoming,previous=previous,endpoint='client')
        if 'Update propagation interrupted' not in log or 'Aborted by user request' not in log:
            raise AssertionError('both original cancellation diagnostics required')
        equal((session.left/name).read_bytes(),previous,'cancellation replaced old live receiver')
        equal((session.right/name).read_bytes(),incoming,'cancellation mutated sending source')
        if session.root.__class__(call['candidate']).exists():raise AssertionError('cancelled validation stage remained resumable')
        session.control(name);session.sync()
        verify_call(session.calls('client')[-1],incoming,previous=previous,endpoint='client')
        no_op(session,name,incoming)
    return cancelled
