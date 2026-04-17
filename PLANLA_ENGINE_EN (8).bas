Attribute VB_Name = "Module_Planla"
Option Explicit

' Public variables to pass data to UserForm
Public g_StartDate As String
Public g_Line As String
Public g_Item As String

' ============================================================
' ENGINE - All calculation and planning logic
' Button macro: Planla
' ============================================================

Private Function SafeParseDate(ByVal s As String) As Long
    s = Trim(s)
    If s = "" Then SafeParseDate = 0: Exit Function
    Dim dd As Integer, mm As Integer, yyyy As Integer
    dd = 0: mm = 0: yyyy = 0
    Dim mTR(1 To 12) As String, mEN(1 To 12) As String
    mTR(1)="ocak":  mTR(2)="subat":   mTR(3)="mart":    mTR(4)="nisan"
    mTR(5)="mayis": mTR(6)="haziran": mTR(7)="temmuz":  mTR(8)="agustos"
    mTR(9)="eylul": mTR(10)="ekim":   mTR(11)="kasim":  mTR(12)="aralik"
    mEN(1)="january":   mEN(2)="february": mEN(3)="march":    mEN(4)="april"
    mEN(5)="may":       mEN(6)="june":     mEN(7)="july":     mEN(8)="august"
    mEN(9)="september": mEN(10)="october": mEN(11)="november":mEN(12)="december"
    Dim sL As String: sL = LCase(s)
    Dim i As Integer
    For i = 1 To 12
        If InStr(sL, mTR(i)) > 0 Or InStr(sL, mEN(i)) > 0 Then
            mm = i
            Dim np As String, ch As String, j As Integer: np = ""
            For j = 1 To Len(s)
                ch = Mid(s, j, 1)
                If ch >= "0" And ch <= "9" Then np = np & ch Else np = np & " "
            Next j
            Dim na() As String: na = Split(Trim(np))
            Dim vn() As String: ReDim vn(0)
            Dim k As Integer
            For k = 0 To UBound(na)
                If Trim(na(k)) <> "" Then
                    ReDim Preserve vn(UBound(vn) + 1)
                    vn(UBound(vn)) = Trim(na(k))
                End If
            Next k
            If UBound(vn) >= 1 Then If CInt(vn(1)) <= 31 Then dd = CInt(vn(1))
            If UBound(vn) >= 2 Then If CInt(vn(2)) > 1000 Then yyyy = CInt(vn(2))
            If dd > 0 And yyyy = 0 Then yyyy = Year(Now)
            If dd > 0 And mm > 0 And yyyy > 0 Then
                On Error Resume Next
                SafeParseDate = CLng(DateSerial(yyyy, mm, dd))
                If Err.Number <> 0 Then SafeParseDate = 0
                On Error GoTo 0
                Exit Function
            End If
        End If
    Next i
    Dim sep As String: sep = ""
    If InStr(s, "/") > 0 Then sep = "/"
    If InStr(s, ".") > 0 Then sep = "."
    If InStr(s, "-") > 0 And sep = "" Then sep = "-"
    If sep <> "" Then
        Dim parts() As String: parts = Split(s, sep)
        If UBound(parts) = 2 Then
            Dim p0 As Integer, p1 As Integer, p2 As Integer
            On Error Resume Next
            p0=CInt(Trim(parts(0))): p1=CInt(Trim(parts(1))): p2=CInt(Trim(parts(2)))
            On Error GoTo 0
            If p0 > 1000 Then
                yyyy=p0: mm=p1: dd=p2
            ElseIf p2 > 1000 Then
                If p0 > 12 Then
                    dd=p0: mm=p1: yyyy=p2
                ElseIf p1 > 12 Then
                    mm=p0: dd=p1: yyyy=p2
                Else
                    dd=p0: mm=p1: yyyy=p2
                End If
            End If
        End If
    End If
    If dd > 0 And mm > 0 And yyyy > 0 Then
        On Error Resume Next
        SafeParseDate = CLng(DateSerial(yyyy, mm, dd))
        If Err.Number <> 0 Then SafeParseDate = 0
        On Error GoTo 0
    End If
End Function

Private Function FindDateCol(ByVal ws As Worksheet, ByVal ts As Long) As Long
    FindDateCol = 0
    If ts = 0 Then Exit Function
    Dim lc As Long: lc = ws.Cells(3, ws.Columns.Count).End(xlToLeft).Column
    Dim col As Long, cv As Variant
    For col = 3 To lc
        cv = ws.Cells(3, col).Value
        If IsDate(cv) Then
            Dim cd As Date: cd = CDate(cv)
            If CLng(DateSerial(Year(cd), Month(cd), Day(cd))) = ts Then
                FindDateCol = col: Exit Function
            End If
        End If
    Next col
    Dim td As Date: td = CDate(ts)
    For col = 3 To lc
        cv = ws.Cells(3, col).Value
        If IsDate(cv) Then
            If Day(CDate(cv)) = Day(td) And _
               Month(CDate(cv)) = Month(td) And _
               Year(CDate(cv)) = Year(td) Then
                FindDateCol = col: Exit Function
            End If
        End If
    Next col
End Function

Private Function GetHR(ByVal lk As String, ByVal ic As String) As Double
    GetHR = 0
    If Not IsNumeric(ic) Then Exit Function
    Dim bom As Worksheet
    On Error Resume Next
    Select Case UCase(lk)
        Case "ETL3": Set bom = ThisWorkbook.Worksheets("ACT BOM TXT")
        Case "ETL5": Set bom = ThisWorkbook.Worksheets("ACT BOM SF")
        Case "ETL6", "ETL7": Set bom = ThisWorkbook.Worksheets("ACT BOM MLY")
    End Select
    On Error GoTo 0
    If bom Is Nothing Then Exit Function
    Dim fc As Range
    Set fc = bom.Rows(1).Find(What:=CLng(ic), LookIn:=xlValues, LookAt:=xlWhole)
    If fc Is Nothing Then Exit Function
    On Error Resume Next
    GetHR = CDbl(bom.Cells(2, fc.Column).Value) * CDbl(bom.Cells(3, fc.Column).Value)
    On Error GoTo 0
End Function

Private Function DoPlanlaSingle(ByVal lk As String, ByVal ic As String, _
    ByVal kg As Double, ByVal sc As Long, ByRef msg As String) As Long
    DoPlanlaSingle = sc: msg = ""
    Dim ws As Worksheet: Set ws = ThisWorkbook.Worksheets("Planning")
    Dim er As Long, hr2 As Long
    Select Case UCase(lk)
        Case "ETL3": er=4:  hr2=6
        Case "ETL5": er=28: hr2=30
        Case "ETL6": er=52: hr2=54
        Case "ETL7": er=76: hr2=78
        Case Else: msg="ERROR: Invalid line " & lk: Exit Function
    End Select
    Dim rate As Double: rate = GetHR(lk, ic)
    If rate <= 0 Then msg="ERROR: " & ic & " not found in BOM (" & lk & ")": Exit Function
    Dim th As Double: th = kg / rate
    ' nd = ceil(th/24) - always enough days so last day <= 24h
    Dim nd As Long
    nd = Int(th / 24)
    If th - nd * 24 > 0 Then nd = nd + 1
    If nd < 1 Then nd = 1
    ' Full days = 24h, last day = exact remaining hours (ceil)
    ReDim ha(1 To nd) As Long
    Dim hi As Long
    For hi = 1 To nd - 1
        ha(hi) = 24
    Next hi
    Dim remH As Double: remH = th - 24 * (nd - 1)
    Dim lastH As Long: lastH = Int(remH)
    If remH - Int(remH) > 0 Then lastH = lastH + 1
    If lastH <= 0 Then lastH = 1
    If lastH > 24 Then lastH = 24
    ha(nd) = lastH
    Dim lc As Long: lc = ws.Cells(3, ws.Columns.Count).End(xlToLeft).Column
    Dim col As Long: col = sc
    Dim di As Long
    For di = 1 To nd
        If col > lc Then msg="WARNING: End of calendar": DoPlanlaSingle=col: Exit Function
        ws.Cells(er, col).Value = CLng(ic)
        ws.Cells(hr2, col).Value = ha(di)
        col = col + 1
    Next di
    Dim det As String: det = ""
    Dim dj As Long
    For dj = 1 To nd
        If dj > 1 Then det = det & "+"
        det = det & ha(dj) & "h"
        If dj=5 And nd>5 Then det=det & "+...": Exit For
    Next dj
    msg = "OK: " & nd & " days  [" & det & "]  " & Format(th,"0.0") & " hrs"
    
    ' Clear duplicate: if same item code continues after our last day, free them
    Dim clearCol As Long: clearCol = col
    Do While clearCol <= lc
        If ws.Cells(er, clearCol).Value = CLng(ic) Then
            ws.Cells(er, clearCol).Value = "Free"
            ws.Cells(hr2, clearCol).Value = 24
            clearCol = clearCol + 1
        Else
            Exit Do
        End If
    Loop
    
    DoPlanlaSingle = col
End Function

Private Function GetActiveVal() As String
    On Error Resume Next
    Dim v As Variant: v = ActiveCell.Value
    If IsDate(v) Then
        GetActiveVal = Format(CDate(v), "dd/mm/yyyy")
    ElseIf IsNumeric(v) Then
        GetActiveVal = CStr(CLng(v))
    Else
        GetActiveVal = CStr(v)
    End If
    On Error GoTo 0
End Function

' ---- Public wrappers for UserForm ----
Public Function SafeParseDatePub(ByVal s As String) As Long
    SafeParseDatePub = SafeParseDate(s)
End Function

Public Function FindDateColPub(ByVal ws As Worksheet, ByVal ts As Long) As Long
    FindDateColPub = FindDateCol(ws, ts)
End Function

Public Function GetHRPub(ByVal lk As String, ByVal ic As String) As Double
    GetHRPub = GetHR(lk, ic)
End Function

Public Function DoPlanlaSinglePub(ByVal lk As String, ByVal ic As String, _
    ByVal kg As Double, ByVal sc As Long, ByRef msg As String) As Long
    DoPlanlaSinglePub = DoPlanlaSingle(lk, ic, kg, sc, msg)
End Function

Public Function GetActiveValPub() As String
    GetActiveValPub = GetActiveVal()
End Function

' ---- Button macro ----
Sub Planla()
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("Planning")
    On Error GoTo 0
    
    Dim ac As Range: Set ac = ActiveCell
    Dim acRow As Long: acRow = ac.Row
    Dim acCol As Long: acCol = ac.Column
    
    ' Detect line from row
    Dim detectedLine As String: detectedLine = ""
    Select Case acRow
        Case 4, 5, 6, 7, 8: detectedLine = "3"
        Case 28, 29, 30, 31, 32: detectedLine = "5"
        Case 52, 53, 54, 55, 56: detectedLine = "6"
        Case 76, 77, 78, 79, 80: detectedLine = "7"
    End Select
    
    ' Detect date from column (row 3)
    Dim detectedDate As String: detectedDate = ""
    If acCol >= 3 And Not ws Is Nothing Then
        Dim dv As Variant: dv = ws.Cells(3, acCol).Value
        If IsDate(dv) Then detectedDate = Format(CDate(dv), "dd/mm/yyyy")
    End If
    
    ' Detect item code from active cell
    Dim detectedItem As String: detectedItem = ""
    Dim cv As Variant: cv = ac.Value
    If IsNumeric(cv) Then
        If CLng(cv) >= 30000 And CLng(cv) <= 39999 Then
            detectedItem = CStr(CLng(cv))
        End If
    End If
    
    ' Set public variables, unload and show fresh
    g_StartDate = detectedDate
    g_Line = detectedLine
    g_Item = detectedItem
    On Error Resume Next
    Unload UserForm1
    On Error GoTo 0
    UserForm1.Show
End Sub
