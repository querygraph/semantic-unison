"""Versioned byte-exact batch capture over the existing bounded drain loop.

Existing measure.CapturedStream and frozen qualification plans stay unchanged.
The owning child wrapper must retain any close/capture uncertainty.
"""
from measure import CapturedStream


class BatchCapture(CapturedStream):
    def __init__(self, stream, limit=4 * 1048576):
        if type(limit) is not int or not 1 <= limit <= 4 * 1048576:
            raise ValueError('bounded batch capture limit required')
        self.finish_attempted = False
        super().__init__(stream, limit)

    def finish_raw(self):
        """One close attempt; preserve original bytes, including invalid UTF8.

        The owning process wrapper must retain uncertainty on any exception;
        this method supplies no process/group settlement authority.
        """
        if self.finish_attempted:
            raise RuntimeError("capture finish already attempted; retain without retry")
        self.finish_attempted = True
        self.thread.join(timeout=2)
        if self.thread.is_alive():
            raise RuntimeError("descendant retained captured output after owned group cleanup")
        self.stream.close()
        if self.error:
            raise RuntimeError("captured output failed: " + self.error)
        return {"bytes": self.total, "truncated": self.total > self.limit,
                "data": b"".join(self.chunks)}

    def finish(self):
        output = self.finish_raw()
        return {"bytes": output["bytes"], "truncated": output["truncated"],
                "text": output["data"].decode("utf-8", "replace")}

    def finish_artifact(self, store, name):
        """Publish only complete raw capture; overflow never qualifies."""
        from batch_artifacts import publish
        output = self.finish_raw()
        if output['truncated'] or len(output['data']) != output['bytes']:
            raise ValueError('capture overflow refuses artifact qualification')
        return publish(store, name, output['data'])

