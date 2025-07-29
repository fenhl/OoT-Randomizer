.headersize(0x800D5EF0 - 0x00B4BE50)

;=============================================================
; Handle playing song of time for switching age. Credits to OOTxMM.
;=============================================================

.org 0x800E157C
    ; Replaces
    ; addiu   $at, $zero, 0x0006
    ; bnel    t3, $at, lbl_800E15AC
    ; addiu   $at, $zero, 0x0029
    ; lw      v0, 0x067C(a3)
    ; addiu   t4, $zero, 0xFF20
    ; sh      t4, 0x0680(a3)
    ; lw      t5, 0x0004(v0)
    ; lui     $at, 0x0001
    ; or      t7, t5, $at
    ; sw      t7, 0x0004(v0)

    sw      a2, 0x0030 (sp)
    sw      a3, 0x0054 (sp)
    sw      t1, 0x0024 (sp)
    lw      a0, 0x0060 (sp)
    or      a1, a3, zero
    jal     Ocarina_HandleLastPlayedSong
    or      a2, t3, zero
    lw      a2, 0x0030 (sp)
    lw      a3, 0x0054 (sp)
    lw      t1, 0x0024 (sp)
