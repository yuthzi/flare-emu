import re

import idaapi
import idautils
import idc
import ida_ida

import flare_emu





class IdaProAnalysisHelper(flare_emu.AnalysisHelper):
    def __init__(self, eh):
        super(IdaProAnalysisHelper, self).__init__()
        self.eh = eh
        try:
            idaapi.get_inf_structure()
            self.init_ida_under_9()
        except AttributeError:
            self.init_ida9()

    def init_ida9(self):
        procname = ida_ida.inf_get_procname()
        if procname == "metapc":
            self.arch = "X86"
        else:
            self.arch = procname

        if ida_ida.inf_is_64bit():
            self.bitness = 64
        elif ida_ida.inf_is_32bit_exactly():
            self.bitness = 32
        else:
            self.bitness = None
        filetype = ida_ida.inf_get_filetype()
        if filetype == 11:
            self.filetype = "PE"
        elif filetype == 25:
            self.filetype = "MACHO"
        elif filetype == 18:
            self.filetype = "ELF"
        else:
            self.filetype = "UNKNOWN"

    def init_ida_under_9(self):
        info = idaapi.get_inf_structure()
        if info.procname == "metapc":
            self.arch = "X86"
        else:
            self.arch = info.procname
        if info.is_64bit():
            self.bitness = 64
        elif info.is_32bit():
            self.bitness = 32
        else:
            self.bitness = None
        if info.filetype == 11:
            self.filetype = "PE"
        elif info.filetype == 25:
            self.filetype = "MACHO"
        elif info.filetype == 18:
            self.filetype = "ELF"
        else:
            self.filetype = "UNKNOWN"

    def getFuncStart(self, addr):
        ret = idc.get_func_attr(addr, idc.FUNCATTR_START)
        if ret == idc.BADADDR:
            return None
        return ret

    def getFuncEnd(self, addr):
        ret =  idc.get_func_attr(addr, idc.FUNCATTR_END)
        if ret == idc.BADADDR:
            return None
        return ret

    def getFuncName(self, addr, normalized=True):
        if normalized:
            return self.normalizeFuncName(idc.get_func_name(addr))
        else:
            return idc.get_func_name(addr)

    def getMnem(self, addr):
        return idc.print_insn_mnem(addr)

    def _getBlockByAddr(self, addr, flowchart):
        for bb in flowchart:
            if (addr >= bb.start_ea and addr < bb.end_ea) or addr == bb.start_ea:
                return bb
        return None

    # gets address of last instruction in the basic block containing addr
    def getBlockEndInsnAddr(self, addr, flowchart):
        bb = self._getBlockByAddr(addr, flowchart)
        return idc.prev_head(bb.end_ea, idc.get_inf_attr(idc.INF_MIN_EA))

    def getMinimumAddr(self):
        return idc.get_inf_attr(idc.INF_MIN_EA)

    def getMaximumAddr(self):
        return idc.get_inf_attr(idc.INF_MAX_EA)

    def getBytes(self, addr, size):
        return idc.get_bytes(addr, size, False)

    def getCString(self, addr):
        buf = ""
        while self.getBytes(addr, 1) != "\x00" and self.getBytes(addr, 1) is not None:
            buf += self.getBytes(addr, 1)
            addr += 1

        return buf

    def getOperand(self, addr, opndNum):
        return idc.print_operand(addr, opndNum)

    def getWordValue(self, addr):
        return idc.get_wide_word(addr)

    def getDwordValue(self, addr):
        return idc.get_wide_dword(addr)

    def getQWordValue(self, addr):
        return idc.get_qword(addr)

    def isThumbMode(self, addr):
        return idc.get_sreg(addr, "T") == 1

    def getSegmentName(self, addr):
        return idc.get_segm_name(addr)

    def getSegmentStart(self, addr):
        return idc.get_segm_start(addr)

    def getSegmentEnd(self, addr):
        return idc.get_segm_end(addr)

    def getSegmentDefinedSize(self, addr):
        size = 0
        segEnd = self.getSegmentEnd(addr)
        addr = self.getSegmentStart(addr)
        while idc.has_value(idc.get_full_flags(addr)):
            if addr >= segEnd:
                break
            size += 1
            addr += 1
        return size

    def getSegments(self):
        return idautils.Segments()

    def getSegmentSize(self, addr):
        return self.getSegmentEnd(addr) - self.getSegmentStart(addr)

    def getSectionName(self, addr):
        return self.getSegmentName(addr)

    def getSectionStart(self, addr):
        return self.getSegmentStart(addr)

    def getSectionEnd(self, addr):
        return self.getSegmentEnd(addr)

    def getSectionSize(self, addr):
        return self.getSegmentSize(addr)

    def getSections(self):
        return self.getSegments()

    # gets disassembled instruction with names and comments as a string
    def getDisasmLine(self, addr):
        return idc.generate_disasm_line(addr, 0)

    def getName(self, addr):
        return idc.get_name(addr, idc.ida_name.GN_VISIBLE)

    def getNameAddr(self, name):
        name = idc.get_name_ea_simple(name)
        if name == "":
            name = idc.get_name_ea_simple(self.normalizeFuncName(name))
        return name

    def getOpndType(self, addr, opndNum):
        return idc.get_operand_type(addr, opndNum)

    def getOpndValue(self, addr, opndNum):
        return idc.get_operand_value(addr, opndNum)

    def makeInsn(self, addr):
        if idc.create_insn(addr) == 0:
            idc.del_items(addr, idc.DELIT_EXPAND)
            idc.create_insn(addr)
        idc.auto_wait()

    def createFunction(self, addr):
        pass

    def getFlowChart(self, addr):
        function = idaapi.get_func(addr)
        return list(idaapi.FlowChart(function))

    def getSpDelta(self, addr):
        f = idaapi.get_func(addr)
        return idaapi.get_sp_delta(f, addr)

    def getXrefsTo(self, addr):
        return list(map(lambda x: x.frm, list(idautils.XrefsTo(addr))))

    def getArch(self):
        return self.arch

    def getBitness(self):
        return self.bitness

    def getFileType(self):
        return self.filetype

    def getInsnSize(self, addr):
        return idc.get_item_size(addr)

    def isTerminatingBB(self, bb):
        if (bb.type == idaapi.fcb_ret or bb.type == idaapi.fcb_noret or
                (bb.type == idaapi.fcb_indjump and len(list(bb.succs())) == 0)):
            return True
        for b in bb.succs():
            if b.type == idaapi.fcb_extern:
                return True

        return False

    def skipJumpTable(self, addr):
        while idc.print_insn_mnem(addr) == "":
            addr = idc.next_head(addr, idc.get_inf_attr(idc.INF_MAX_EA))
        return addr

    def setName(self, addr, name, size=0):
        idc.set_name(addr, name, idc.SN_NOCHECK)

    def setComment(self, addr, comment, repeatable=False):
        idc.set_cmt(addr, comment, repeatable)

    def normalizeFuncName(self, funcName):
        # remove appended _n from IDA Pro names
        funcName = re.sub(r"_[\d]+$", "", funcName)
        return funcName
