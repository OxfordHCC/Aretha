class Extposure:
    def __init__(self, initial=None):
        self.packets = 0
        self.bytes = 0
        self.bytevar = 0
        self.ext = initial.ext
        self.merge(initial)
        
    def merge(self, transmission):
        assert transmission.ext == self.ext, f"Ext mismatch {self.ext} vs {transmission.ext}"
        self.packets += transmission.packets
        self.bytes += transmission.bytes
        self.bytevar = self._combinevar(self.bytevar, transmission.bytevar)
        return self

    def _combinevar(self, v1, v2):
        return v1 + v2  # TODO

    def to_dict(self):
        return dict( [ (x, self.__getattribute__(x)) for x in ['packets','bytes','bytevar'] ] )
        
class TransMac:
    # mac -> ip exposure
    def __init__(self, tnew):
        self.mac = tnew.mac
        self.by_ext = {}
        self.merge(tnew)

    def merge(self, transmission):
        assert self.mac == transmission.mac, f"internal error: Mac mismatch { self.mac } vs { transmission.mac }"
        self.by_ext[transmission.ext] = self.by_ext.get(transmission.ext) and self.by_ext.get(transmission.ext).merge(transmission) or Extposure(transmission)
        return self

    def to_dict(self):
        return dict([(k,e.to_dict()) for (k,e) in self.by_ext.items()])

class TransEpoch:
    # transepoch has by_mac -> ext
    def __init__(self, transmission=None):
        self.by_mac = {}
        if not transmission is None:
            self.merge(transmission)
        
    def merge(self, transmission):
        tx_mac = self.by_mac.get(transmission.mac)
        if tx_mac is None:
            tx_mac = TransMac(transmission)
        else:
            tx_mac = tx_mac.merge(transmission)

        self.by_mac[transmission.mac] = tx_mac
        
        return self

    def to_dict(self):
        return dict([(mac, trans.to_dict()) for (mac, trans)  in self.by_mac.items()])
    
        
class TransmissionMerger:
    def __init__(self, mins=5):
        self.by_epoch = {}
        self.mins = mins

    def compute_epoch(self, dt):
        # computes the relevant epoch of dt
        return math.floor(dt.timestamp() / (self.mins*60))

    def merge(self, transmission):
        # transmission has to be a peeweemodel joined
        assert transmission.exposure and transmission.exposure.id, "Model must be joined with Exposures"
        epoch = self.compute_epoch(transmission.exposure.start_date)
        if self.by_epoch.get(epoch):
            self.by_epoch[epoch].merge(transmission)
        else:
            self.by_epoch[epoch] = TransEpoch(transmission)

    def iter_by_epoch(self):
        return [x for x in sorted(self.by_epoch.items())]

    def to_dict(self):
        return dict([(epoch, macset.to_dict()) for (epoch, macset) in self.by_epoch.items()])
        
