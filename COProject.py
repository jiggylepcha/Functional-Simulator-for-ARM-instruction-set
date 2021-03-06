#CO Project
#Arm Simulator
#Vishaal Udandarao 2016119
#Suryatej Reddy 2016102
#Jigme Lobsang lepcha 2016045

import sys

class Instruction:
    all_instructions = list()
    registers = dict()
    memory = dict()
    # if res==0, op1==op2, res>0, op1>op2 and res<0, op1<op2
    compare_difference = 0
    program_counter = 0
    sp = []
    isStackPointer = False
    isLoadStackPointer = False
    isStoreStackPointer = False

    TYPE_DATA_PROCESSING = 0
    TYPE_SINGLE_DATA_TRANSFER = 1

    def __init__(self,addr,inst):
        self.addressInHex = addr
        self.addressInInt = getIntFromHex(addr)
        self.instruction = inst
        self.instructionInBinary = getBinaryFromHex(inst)[2:]
        self.subInstruction = None
        Instruction.all_instructions.append(self)

    @staticmethod
    def getInstruction(address):
        return next((instruct for instruct in Instruction.all_instructions if instruct.addressInInt == address), None)

    def printFetchStatement(self):
        print ("FETCH : Fetch instruction " + self.instruction + " from address " + self.addressInHex)

    def splitInstruction(self):
        instructionInBinary = self.instructionInBinary
        format_bits = instructionInBinary[4:6]  #27,26
        format_bits_for_branch = instructionInBinary[4:8] #27,26,25,24
        condition_code = instructionInBinary[:4]

        if (format_bits == '00'):
            #data processing instruction
            Instruction.program_counter += 4
            Instruction.registers[15] = Instruction.program_counter
            dataInstruction = DataProcessingInstruction(self)
            self.subInstruction=dataInstruction

        elif (format_bits == '01'):
            #single data transfer
            dataTransferInstruction = SingleDataTransferInstruction(self)
            self.subInstruction = dataTransferInstruction
            Instruction.program_counter += 4
            Instruction.registers[15] = Instruction.program_counter

        elif (format_bits_for_branch == '1010'):
            #branch operation with corresponding condition code
            branchInstruction = BranchInstruction(self)
            self.subInstruction = branchInstruction
        elif (format_bits_for_branch == '1111'):
            swiInstruction = SWIInstruction(self)
            self.subInstruction = swiInstruction

        else:
            Instruction.program_counter += 4
            Instruction.registers[15] = Instruction.program_counter


class SWIInstruction:

    TYPE_INPUT = 108
    TYPE_PRINT = 107
    TYPE_EXIT = 17

    def __init__(self,instruction):
        self.instruction = instruction
        self.type = ""
        self.assignValues()

    def assignValues(self):
        instructionInBinary = self.instruction.instructionInBinary
        lastByte = instructionInBinary[24:]
        typeInInt = int(lastByte,2)
        if (typeInInt == SWIInstruction.TYPE_INPUT):
            print ("DECODE: Input Instruction")
            print ("Read Regsiters: None")
            print ("EXECUTE:")
            if (Instruction.registers.get(0) == 0):
                n = input("Taking Input \n")
                Instruction.registers[0] = int(n)
                print ("MEMORY: No Memory Operation")
                print ("WRITEBACK: write Input Value to R0")
            else:
                print("Invalid Choice For Input")
            Instruction.program_counter += 4
            Instruction.registers[15] = Instruction.program_counter
        elif (typeInInt == SWIInstruction.TYPE_PRINT):
            if (Instruction.registers.get(0) == 1):
                print("DECODE: Print Instruction")
                print("Read Regsiters: None")
                print ("EXECUTE : STDOUT - " + str(Instruction.registers.get(1)))
            else:
                print ("Invalid Print Statement")
            print("MEMORY: No Memory Operation")
            print("WRITEBACK : No Writeback")
            Instruction.program_counter += 4
            Instruction.registers[15] = Instruction.program_counter
        elif (typeInInt == SWIInstruction.TYPE_EXIT):
            print ("EXIT:")
            sys.exit()

class BranchInstruction:

    CODE_EQ = '0000'
    CODE_NE = '0001'
    CODE_GE = '1010'
    CODE_LT = '1011'
    CODE_GT = '1100'
    CODE_LE = '1101'
    CODE_AL = '1110'

    def __init__(self,instruction):
        self.instruction = instruction
        self.condition = ""
        self.offset = ""
        self.assignValues()
        self.executeInstruction()

    def assignValues(self):
        instructionInBinary = self.instruction.instructionInBinary
        condition = instructionInBinary[:4]  # 31,30,29,28
        self.condition = condition
        self.offset = instructionInBinary[8:]

    def getType(self):
        if self.condition == BranchInstruction.CODE_EQ:
                return "BEQ"
        elif self.condition == BranchInstruction.CODE_NE:
                return "BNE"
        elif self.condition == BranchInstruction.CODE_GE:
                return "BGE"
        elif self.condition == BranchInstruction.CODE_LT:
                return "BLT"
        elif self.condition == BranchInstruction.CODE_GT:
                return "BGT"
        elif self.condition == BranchInstruction.CODE_LE:
                return "BLE"
        elif self.condition == BranchInstruction.CODE_AL:
                return "BAL"

    def twos_comp(self,val, bits):

        if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
            val = val - (1 << bits)  # compute negative value
        return val


    def executeInstruction(self):
        compare_difference = Instruction.compare_difference
        offset_to_be_used=self.twos_comp(int(self.offset,2) , len(self.offset))*4
        if(self.condition == BranchInstruction.CODE_EQ):
            if(compare_difference == 0):
                Instruction.program_counter+=offset_to_be_used+4
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(Instruction.program_counter))
                print('EXECUTE : BEQ '+hex(Instruction.program_counter)+", Branch Taken")
            else:
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(int(Instruction.program_counter + int(offset_to_be_used))))
                print("EXECUTE : BEQ "+hex(int(Instruction.program_counter + offset_to_be_used))+", Branch Not Taken")
                Instruction.program_counter+=4
                return
        elif(self.condition == BranchInstruction.CODE_NE):
            if(compare_difference != 0):
                Instruction.program_counter +=  offset_to_be_used +4
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(Instruction.program_counter))
                print('EXECUTE : BNE ' + hex(Instruction.program_counter)+", Branch Taken")
            else:
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(int(Instruction.program_counter + int(offset_to_be_used))))
                print("EXECUTE : BEQ " + hex(int(Instruction.program_counter + int(offset_to_be_used))) + ", Branch Not Taken")
                Instruction.program_counter+=4
                return
        elif(self.condition == BranchInstruction.CODE_GE):

            if(compare_difference >= 0):
                Instruction.program_counter +=  offset_to_be_used+4
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(Instruction.program_counter))
                print('EXECUTE : BGE ' + hex(Instruction.program_counter)+", Branch Taken")
            else:
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(int(Instruction.program_counter + int(offset_to_be_used))))
                print("EXECUTE : BEQ " + hex(int(Instruction.program_counter + int(offset_to_be_used))) + ", Branch Not Taken")
                Instruction.program_counter+=4
                return
        elif(self.condition == BranchInstruction.CODE_LT):
            if(compare_difference < 0):
                Instruction.program_counter +=  int(offset_to_be_used)+4
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(Instruction.program_counter))
                print('EXECUTE : BLT ' + hex(Instruction.program_counter)+", Branch Taken")
            else:
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(int(Instruction.program_counter + int(offset_to_be_used))))
                print("EXECUTE : BEQ " + hex(int(Instruction.program_counter + int(offset_to_be_used))) + ", Branch Not Taken")
                Instruction.program_counter+=4
                return
        elif(self.condition == BranchInstruction.CODE_GT):
            if(compare_difference > 0):
                Instruction.program_counter +=  int(offset_to_be_used)+4
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(Instruction.program_counter))
                print('EXECUTE : BGT ' + hex(Instruction.program_counter)+", Branch Taken")
            else:
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(int(Instruction.program_counter + int(offset_to_be_used))))
                print("EXECUTE : BEQ " + hex(int(Instruction.program_counter + int(offset_to_be_used))) + ", Branch Not Taken")
                Instruction.program_counter+=4
                return
        elif(self.condition == BranchInstruction.CODE_LE):
            if(compare_difference <= 0):
                Instruction.program_counter +=  int(offset_to_be_used)+4
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(Instruction.program_counter))
                print('EXECUTE : BLE ' + hex(Instruction.program_counter)+", Branch Taken")
            else:
                print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(int(Instruction.program_counter + int(offset_to_be_used))))
                print("EXECUTE : BEQ " + hex(int(Instruction.program_counter + int(offset_to_be_used))) + ", Branch Not Taken")
                Instruction.program_counter+=4
                return
        elif(self.condition == BranchInstruction.CODE_AL):
            Instruction.program_counter +=  offset_to_be_used+4

            print("DECODE : Operation is " + self.getType() + ", Address to move to is " + hex(Instruction.program_counter))
            print('EXECUTE : B(AL) ' + hex(Instruction.program_counter)+", Branch Taken")
        Instruction.registers[15] = Instruction.program_counter
        print("MEMORY : No memory operation")
        print("WRITEBACK : No writeback operation")




class DataProcessingInstruction:



    OPERAND_TYPE_REGISTER = '0'
    OPERAND_TYPE_IMMEDIATE = '1'
    SHIFT_TYPE_LOGICAL_LEFT = "00"
    SHIFT_TYPE_LOGICAL_RIGHT = "01"
    SHIFT_TYPE_ARITHMETIC_RIGHT = "10"
    SHIFT_TYPE_ROTATE_RIGHT = "11"

    OPCODE_AND = '0000'
    OPCODE_EOR = '0001'
    OPCODE_SUB = '0010'
    OPCODE_RSB = '0011'
    OPCODE_ADD = '0100'
    OPCODE_ORR = '1100'
    OPCODE_MOV = '1101'
    OPCODE_BIC = '1110'
    OPCODE_MVN = '1111'
    OPCODE_CMP = '1010'


    def __init__(self,instruction):
        self.instruction = instruction
        self.condition = ""
        self.opcode = ""
        self.sourceRegister1 = None
        self.sourceRegister2 = None
        self.destination_register = None
        self.immediateValue = None
        self.typeOfOperand = ""
        self.operand_1 = 0
        self.operand_2 = 0
        self.shift = 0
        self.rotate = 0
        self.type = None
        self.assignValues()
        self.executeInstruction()





    def assignValues(self):
        instructionInBinary = self.instruction.instructionInBinary
        condition = instructionInBinary[:4]  #31,30,29,28
        self.condition = condition
        self.type = Instruction.TYPE_DATA_PROCESSING
        self.typeOfOperand = instructionInBinary[6:7]
        self.opcode = instructionInBinary[7:11]
        self.sourceRegister1 = instructionInBinary[12:16]
        self.operand_1 = Instruction.registers[int(self.sourceRegister1,2)]
        Instruction.isStackPointer=False
        if(self.sourceRegister1 == '1101'):
            Instruction.isStackPointer = True


        self.destination_register = instructionInBinary[16:20]
        instructionInBinary = self.instruction.instructionInBinary
        if (str(self.typeOfOperand) == str(DataProcessingInstruction.OPERAND_TYPE_REGISTER) and Instruction.isStackPointer==False):
            self.shift = instructionInBinary[20:28]
            self.sourceRegister2 = instructionInBinary[28:]
            self.operand_2 = Instruction.registers[int(self.sourceRegister2,2)]

            print("DECODE : Operation is " + self.getTypeOfInstruction() + ", First Operand is  R" + str(
                int(self.sourceRegister1, 2)) + " , Second Operand is R" + str(
                int(self.sourceRegister1, 2)) + " ,Destination Register is R" + str(
                int(self.destination_register, 2)) + ".")

            print("Read Registers: R" + str(int(self.sourceRegister1,2)) + " = " +
                   str(Instruction.registers[int(self.sourceRegister1,2)]) + " , R"
                   + str(int(self.sourceRegister2,2)) + " = " + str(Instruction.registers[int(self.sourceRegister2,2)]))



            shiftOperation = self.shift[7]
            if (str(shiftOperation) == "0"):
                ror = lambda val, r_bits, max_bits: \
                    ((val & (2 ** max_bits - 1)) >> r_bits % max_bits) | \
                    (val << (max_bits - (r_bits % max_bits)) & (2 ** max_bits - 1))
                #instruction specified shift amount
                shiftAmount = self.shift[:5]
                shiftAmount = int(shiftAmount,2)
                shiftType = self.shift[5:7]
                if (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_LOGICAL_LEFT):
                    self.operand_2 = self.operand_2 << shiftAmount
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_LOGICAL_RIGHT):
                    self.operand_2 = self.operand_2 >> shiftAmount
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_ARITHMETIC_RIGHT):
                    self.operand_2 = rshift(self.operand_2,shiftAmount)
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_ROTATE_RIGHT):
                    self.operand_2 = ror(self.operand_2, shiftAmount, 64)
                    #TODO Apply ASR and ROR


            elif (str(shiftOperation) == "1"):
                ror = lambda val, r_bits, max_bits: \
                    ((val & (2 ** max_bits - 1)) >> r_bits % max_bits) | \
                    (val << (max_bits - (r_bits % max_bits)) & (2 ** max_bits - 1))
                shiftRegister = self.shift[:4]
                shiftAmount = Instruction.registers[int(shiftRegister,2)]
                shiftAmount = shiftAmount & 255
                shiftType = self.shift[5:7]
                if (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_LOGICAL_LEFT):
                    self.operand_2 = self.operand_2 << shiftAmount
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_LOGICAL_RIGHT):
                    self.operand_2 = self.operand_2 >> shiftAmount
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_ARITHMETIC_RIGHT):
                    self.operand_2 = rshift(self.operand_2, shiftAmount)
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_ROTATE_RIGHT):
                    self.operand_2 = ror(self.operand_2, shiftAmount, 64)




        elif (str(self.typeOfOperand) == str(DataProcessingInstruction.OPERAND_TYPE_IMMEDIATE)):
            self.rotate = instructionInBinary[20:24]
            self.immediateValue = instructionInBinary[24:]
            self.operand_2 = int(self.immediateValue,2)


            if (self.getTypeOfInstruction() != "MOV"):
                if(Instruction.isStackPointer):
                    print("DECODE : Operation is "+self.getTypeOfInstruction() + ", First operand is sp(Stack Pointer)"+" , immediate Second Operand is "+str(self.operand_2)+".")
                    print("Read Registers: R13(sp)")
                else:
                    print("DECODE : Operation is " + self.getTypeOfInstruction() + ", First Operand is  R" + str(int(self.sourceRegister1, 2)) + " , immediate Second Operand is " + str(self.operand_2) + " ,Destination Register is R" + str(int(self.destination_register, 2)) + ".")
                    print("Read Registers: R" + str(int(self.sourceRegister1, 2)) + " = " +str(Instruction.registers[int(self.sourceRegister1, 2)]))

            else:

                print("DECODE : Operation is " + self.getTypeOfInstruction() + ", First Operand is  R" + str(int(self.sourceRegister1, 2)) + " , Immediate Operand is " + str(
                    self.operand_2) + " ,Destination Register is R" + str(
                    int(self.destination_register, 2)) + ".")

                print("Read Registers: None")

    def getTypeOfInstruction(self):
        if self.opcode == DataProcessingInstruction.OPCODE_AND:
                return "AND"
        elif self.opcode == DataProcessingInstruction.OPCODE_EOR:
                return "EOR"
        elif self.opcode == DataProcessingInstruction.OPCODE_SUB:
                return "SUB"
        elif self.opcode == DataProcessingInstruction.OPCODE_RSB:
                return "RSB"
        elif self.opcode == DataProcessingInstruction.OPCODE_ADD:
                return "ADD"
        elif self.opcode == DataProcessingInstruction.OPCODE_ORR:
                return "ORR"
        elif self.opcode == DataProcessingInstruction.OPCODE_MOV:
                return "MOV"
        elif self.opcode == DataProcessingInstruction.OPCODE_BIC:
                return "BIC"
        elif self.opcode == DataProcessingInstruction.OPCODE_MVN:
                return "MVN"
        elif self.opcode == DataProcessingInstruction.OPCODE_CMP:
                return "CMP"



    def executeInstruction(self):
        res = 0
        if self.opcode == DataProcessingInstruction.OPCODE_AND:
                res = self.operand_1 & self.operand_2
                Instruction.registers[int(self.destination_register,2)] = res
                print('EXECUTE : AND '+str(self.operand_1)+' and '+str(self.operand_2))
        elif self.opcode == DataProcessingInstruction.OPCODE_EOR:
                res = self.operand_1 ^ self.operand_2
                Instruction.registers[int(self.destination_register,2)] = res
                print('EXECUTE : EOR '+str(self.operand_1)+' and '+str(self.operand_2))
        elif self.opcode == DataProcessingInstruction.OPCODE_SUB:

                if(Instruction.isStackPointer):
                    for i in range(self.operand_2):
                        #store 0 in stack by default
                        Instruction.sp.append(0)
                    print("EXECUTE : Grow stack by "+str(self.operand_2)+" bytes.")
                else:
                    res = self.operand_1 - self.operand_2
                    Instruction.registers[int(self.destination_register,2)] = res
                    print('EXECUTE : SUB '+str(self.operand_1)+' and '+str(self.operand_2))
        elif self.opcode == DataProcessingInstruction.OPCODE_RSB:
                res = self.operand_2 - self.operand_1
                Instruction.registers[int(self.destination_register,2)] = res
                print('EXECUTE : RSB '+str(self.operand_2)+' and '+str(self.operand_1))
        elif self.opcode == DataProcessingInstruction.OPCODE_ADD:

                if(Instruction.isStackPointer):
                    for i in range(self.operand_2):
                        if(len(Instruction.sp)>0):
                            Instruction.sp.pop()
                        else:
                            print("Stack Underflow. Stack emptied.")
                    print("EXECUTE : Delete "+str(self.operand_2)+" bytes from stack(sp).")
                else:
                    res = self.operand_1 + self.operand_2
                    Instruction.registers[int(self.destination_register,2)] = res
                    print('EXECUTE : ADD '+str(self.operand_1)+' and '+str(self.operand_2))

        elif self.opcode == DataProcessingInstruction.OPCODE_ORR:
                res = self.operand_1 | self.operand_2
                Instruction.registers[int(self.destination_register,2)] = res
                print('EXECUTE : ORR '+str(self.operand_1)+' and '+str(self.operand_2))
        elif self.opcode == DataProcessingInstruction.OPCODE_MOV:
                res = self.operand_2
                Instruction.registers[int(self.destination_register,2)] = res
                print('EXECUTE : MOV '+str(self.operand_2)+' in R'+str(int(self.destination_register,2)))
        elif self.opcode == DataProcessingInstruction.OPCODE_BIC:
                res = self.operand_1 & (~self.operand_2)
                Instruction.registers[int(self.destination_register,2)] = res
                print('EXECUTE : BIC '+str(self.operand_1)+' and '+str(self.operand_2))
        elif self.opcode == DataProcessingInstruction.OPCODE_MVN:
                res = ~self.operand_2
                Instruction.registers[int(self.destination_register,2)] = res
                print('EXECUTE : MVN '+str(self.operand_2)+' in R'+str(int(self.destination_register,2)))

        elif self.opcode == DataProcessingInstruction.OPCODE_CMP:
                res = self.operand_1 - self.operand_2
                Instruction.compare_difference = res
                print('EXECUTE : CMP '+str(self.operand_1)+' and '+str(self.operand_2))


        print("MEMORY: No memory operation")
        if(Instruction.isStackPointer or self.getTypeOfInstruction() == "CMP"):
            print("WRITEBACK : No writeback operation")
        else:
            print("WRITEBACK: write " + str(res) + " to R" + str(int(self.destination_register, 2)))



class SingleDataTransferInstruction:


    def __init__(self,instruction):
        self.instruction = instruction

        self.condition = ""
        self.immediateOffset = ""
        self.indexingBit = ""
        self.upDownBit = ""
        self.byteWordBit = ""
        self.writeBackBit = ""
        self.loadStoreBit = ""
        self.baseRegister = None
        self.destinationRegister = None
        self.offset = None

        self.assignValues()



    def assignValues(self):
        instructionInBinary = self.instruction.instructionInBinary
        condition = instructionInBinary[:4]  #31,30,29,28
        self.condition = condition
        self.immediateOffsetCheck = instructionInBinary[6:7] #25
        self.indexingBit = instructionInBinary[7:8] #24
        self.upDownBit = instructionInBinary[8:9] #23
        self.byteWordBit = instructionInBinary[9:10] #22
        self.writeBackBit = instructionInBinary[10:11] #21
        self.loadStoreBit = instructionInBinary[11:12] #20
        self.baseRegister = instructionInBinary[12:16] #19,18,17,16
        self.destinationRegister = instructionInBinary[16:20] #15,14,13,12

        Instruction.isLoadStackPointer = False
        Instruction.isStoreStackPointer = False
        if(self.loadStoreBit == "0" and self.baseRegister == '1101'):
            Instruction.isStoreStackPointer = True
        elif(self.baseRegister == '1101'):
            Instruction.isLoadStackPointer = True


        if (self.immediateOffsetCheck == "0"):
            #immediate offset
            immediateOffset = instructionInBinary[20:32]
            self.offset = int(immediateOffset,2)

        else:
            #offset is a register
            shiftToRegister = instructionInBinary[20:28]
            offsetRegister = instructionInBinary[28:32]

            self.offset = Instruction.registers[int(offsetRegister,2)]

            shiftOperation = shiftToRegister[7]
            if (str(shiftOperation) == "0"):
                ror = lambda val, r_bits, max_bits: \
                    ((val & (2 ** max_bits - 1)) >> r_bits % max_bits) | \
                    (val << (max_bits - (r_bits % max_bits)) & (2 ** max_bits - 1))

                # instruction specified shift amount
                shiftAmount = shiftToRegister[:5]
                shiftAmount = int(shiftAmount, 2)
                shiftType = shiftToRegister[5:7]
                if (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_LOGICAL_LEFT):
                    self.offset = self.offset << shiftAmount
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_LOGICAL_RIGHT):
                    self.offset = self.offset >> shiftAmount
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_ARITHMETIC_RIGHT):
                    self.offset = rshift(self.offset, shiftAmount)
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_ROTATE_RIGHT):
                    self.offset = ror(self.offset,shiftAmount,64)


            elif (str(shiftOperation) == "1"):

                # TODO register shift
                # register specified shift amount

                ror = lambda val, r_bits, max_bits: \
                    ((val & (2 ** max_bits - 1)) >> r_bits % max_bits) | \
                    (val << (max_bits - (r_bits % max_bits)) & (2 ** max_bits - 1))
                shiftRegister = shiftToRegister[:4]
                shiftAmount = Instruction.registers[int(shiftRegister, 2)]
                shiftAmount = shiftAmount & 255
                shiftType = shiftRegister[5:7]
                if (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_LOGICAL_LEFT):
                    self.offset = self.offset << shiftAmount
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_LOGICAL_RIGHT):
                    self.offset = self.offset >> shiftAmount
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_ARITHMETIC_RIGHT):
                    self.offset = rshift(self.offset, shiftAmount)
                elif (str(shiftType) == DataProcessingInstruction.SHIFT_TYPE_ROTATE_RIGHT):
                    self.offset = ror(self.offset, shiftAmount, 64)

        baseAddress = Instruction.registers[int(self.baseRegister,2)]


        if (self.indexingBit == "1"):
            #pre indexed

            if (self.upDownBit == "1"):   #add the offset
                baseAddress += self.offset
            else:
                baseAddress -= self.offset #subtract the offset

            if (Instruction.isLoadStackPointer or Instruction.isStoreStackPointer):
                self.printDecodeStatementForStack()
                self.loadStoreForStack(baseAddress)
                return

            if (self.writeBackBit == "0"):
                #no write back
                pass
            else:
                #write back
                Instruction.registers[int(self.baseRegister,2)] = baseAddress

            self.printDecodeStatement()
            self.performLoadStore(baseAddress)

        else:
            #post indexed

            self.printDecodeStatement()
            self.performLoadStore(baseAddress)

            if (self.upDownBit == "1"):  # add the offset
                baseAddress += self.offset
            else:
                baseAddress -= self.offset  # subtract the offset

            Instruction.registers[int(self.baseRegister,2)] = baseAddress

    def performLoadStore(self,base_address):
        if (self.loadStoreBit == "0"): #store to memory
            Instruction.memory[base_address] = Instruction.registers[int(self.destinationRegister,2)]
            print ("MEMORY: Storing " + str(Instruction.registers[int(self.destinationRegister,2)]) + " at the memory location " + str(base_address))
            print ("WRITEBACK: No WriteBack")

        else: #load from memory
            loaded_value = Instruction.memory.get(base_address,None)
            if (loaded_value == None):
                Instruction.memory[base_address] = 0
                loaded_value = 0
            Instruction.registers[int(self.destinationRegister,2)] = loaded_value
            print("MEMORY: Loading from memory location " + str(base_address) + " and storing in  R" + str(int(self.destinationRegister,2)))
            print("WRITEBACK: write " + str(loaded_value) + " to R" + str(int(self.destinationRegister,2)))


    def printDecodeStatement(self):
        if (self.loadStoreBit ==  "0"): #Store to memory
            print("DECODE : Operation is STORE, Base Register is R" + str(int(self.baseRegister,2)) + ", Source Register is R" + str(int(self.destinationRegister,2)) + ".")
            print("Read Registers: R" + str(int(self.baseRegister,2)) + " = " + str(Instruction.registers[int(self.baseRegister,2)]) + " , R" + str(int(self.destinationRegister,2)) + " = " + str(Instruction.registers[int(self.destinationRegister,2)]) + " .")
        else:
            print("DECODE: Operation is LOAD, Base Register is R" + str(int(self.baseRegister,2)) + ", Destination Register is R" + str(int(self.destinationRegister,2)) + ".")
            print("Read Registers: R" + str(int(self.baseRegister, 2)) + " = " + str(Instruction.registers[
                int(self.baseRegister, 2)]) )
        print("EXECUTE : No Execute Operation")

    def loadStoreForStack(self, baseAddress):
        if(self.loadStoreBit == "0"):

            if(len(Instruction.sp)>int(self.offset/4)):
                Instruction.sp[int(self.offset/4)]=Instruction.registers[int(self.destinationRegister, 2)]
                print("MEMORY: Storing " + str(Instruction.registers[int(self.destinationRegister, 2)]) + "in stack")
            else:
                print("Stack overflow error.")
            print("WRITEBACK: No WriteBack")
        else:
            if(len(Instruction.sp)>int(self.offset/4)):
                loaded_value=Instruction.sp[int(self.offset/4)]
                Instruction.registers[int(self.destinationRegister, 2)] = loaded_value
                print("MEMORY: Loading from stack and storing in  R" + str(int(self.destinationRegister, 2)))
                print("WRITEBACK: write " + str(loaded_value) + " to R" + str(int(self.destinationRegister, 2)))
            else:
                print("Stack location requested does not exist.")

    def printDecodeStatementForStack(self):
        if (self.loadStoreBit ==  "0"): #Store to memory
            print("DECODE : Operation is STORE, Base Register is R13(sp)"  + ", Source Register is R" + str(int(self.destinationRegister,2)) + ".")
            print("Read Registers: R" + str(int(self.destinationRegister,2)) + " = " + str(Instruction.registers[int(self.destinationRegister,2)]) + " .")
        else:
            print("DECODE: Operation is LOAD, Base Register is R13(sp)" + ", Destination Register is R" + str(int(self.destinationRegister,2)) + ".")
            print("Read Registers: R13(sp)")
        print("EXECUTE : No Execute Operation")


def getIntFromHex(hexValue):
    return int(hexValue,16)

def getBinaryFromHex(hexValue):
    return format(int(hexValue, 16), "#034b")


def rshift(val, n):
    return (val % 0x100000000) >> n


#returns dictionary
def initRegisters(numberOfRegisters = 32):
    registers = dict()
    for reigsterId in range(0,numberOfRegisters):
            registers[reigsterId] = 0
            Instruction.registers = registers

#returns List
def initMainMemory():
        memory = dict()
        Instruction.memory = memory


#the dictionary contains {0:('0x0xE3A0200A',0x0),4:('0x0xE3A0200A',0x4)}
def loadFromFile(fileName):
    file = open(fileName,'r')
    allInstructions = file.readlines()
    for data in allInstructions:
        instruct = data.split()
        addressInHex = instruct[0].strip()
        instruction = instruct[1].strip()
        tempInstruction = Instruction(addressInHex,instruction)
    return len(allInstructions)

#just prints instruction and returns the instruction
def fetchInstruction(instLocation):
        curInstruction = Instruction.getInstruction(instLocation)
        # curInstruction.printFetchStatement()
        return curInstruction

#takes the instruction object as a parameter
def decodeInstruction(instruction):
        pass

def main():

    size=loadFromFile("input.mem")
    initMainMemory()
    initRegisters(16)

    while(Instruction.program_counter<=(size*4)-1):
        currentInstruction = fetchInstruction(Instruction.program_counter)
        currentInstruction.printFetchStatement()
        currentInstruction.splitInstruction()
        print("PC:",Instruction.registers[15])
        print ("Register File : " + str(Instruction.registers))
        print ("Global Memory : " + str(Instruction.memory))
        print ("----------------------------------------------")
if __name__=='__main__':
    main()
