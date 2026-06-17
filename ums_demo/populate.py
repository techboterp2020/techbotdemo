"""Programmatic demo-data generator for the UMS suite.

Creates 25+ records on every screen through the ORM so that all constraints,
sequences and computed fields behave exactly as in production.

Every create that could fail is wrapped in its own savepoint via ``_guard`` so a
single bad row is logged and skipped without poisoning the transaction or
aborting the rest of the load. Idempotent via a sentinel institution code.
"""
import logging
from contextlib import contextmanager
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)

SENTINEL_CODE = 'DEMO-U1'

EN_FIRST = ['Mohammed', 'Ahmed', 'Abdullah', 'Sara', 'Fatimah', 'Noura', 'Khalid',
            'Reem', 'Abdulaziz', 'Lama', 'Fahd', 'Hind', 'Sultan', 'Jawaher', 'Yasser']
EN_LAST = ['Al-Saud', 'Al-Qahtani', 'Al-Ghamdi', 'Al-Otaibi', 'Al-Shehri',
           'Al-Dossari', 'Al-Harbi', 'Al-Zahrani', 'Al-Mutairi', 'Al-Subaie']


@contextmanager
def _guard(env, label):
    """Isolate a unit of work in a savepoint; log and swallow any failure."""
    try:
        with env.cr.savepoint():
            yield
    except Exception:
        _logger.exception("UMS demo: '%s' failed (skipped)", label)


def _name(i, salt=0):
    return '%s %s' % (EN_FIRST[(i + salt) % len(EN_FIRST)],
                      EN_LAST[(i + salt) % len(EN_LAST)])


class _Ctx:
    def __init__(self):
        self.institutions, self.colleges, self.departments = [], [], []
        self.programs, self.courses, self.plans = [], [], []
        self.plos = {}
        self.years, self.terms, self.current_term = [], [], None
        self.rooms, self.slots, self.instructors, self.sections = [], [], [], []
        self.students, self.intakes, self.current_intake, self.faculty = [], [], None, []


def generate(env):
    if env['ums.institution'].sudo().search([('code', '=', SENTINEL_CODE)], limit=1):
        _logger.info("UMS demo data already present; skipping generation.")
        return
    env = env(context=dict(env.context, tracking_disable=True, mail_create_nolog=True))
    ctx = _Ctx()
    _logger.info("UMS demo: generating records...")
    for step in (_structure, _catalog, _study_plans, _calendar, _people, _sections,
                 _students, _registrations_and_grades, _holds_and_advising,
                 _admissions, _teaching, _assessment_config, _finance, _faculty_load,
                 _graduation, _credentials, _analytics, _accreditation, _pathways,
                 _pdpl_and_audit):
        step(env, ctx)
    _logger.info("UMS demo: generation complete.")


# ---------------------------------------------------------------- structure ---
def _structure(env, ctx):
    Inst = env['ums.institution']
    for code, en, ar, vat in [
            (SENTINEL_CODE, 'Riyadh International University', 'جامعة الرياض الدولية', '300000000000003'),
            ('DEMO-U2', 'Jeddah Science College', 'كلية جدة للعلوم', '300000000000004')]:
        with _guard(env, 'institution %s' % code):
            ctx.institutions.append(Inst.create({
                'code': code, 'name_en': en, 'name_ar': ar, 'vat': vat}))
    if not ctx.institutions:
        return
    College = env['ums.college']
    for code, en, ar, inst_idx in [
            ('ENG', 'College of Engineering', 'كلية الهندسة', 0),
            ('CSI', 'College of Computer & Information', 'كلية الحاسب والمعلومات', 0),
            ('BUS', 'College of Business', 'كلية إدارة الأعمال', 0),
            ('SCI', 'College of Sciences', 'كلية العلوم', 0),
            ('MED', 'College of Health Sciences', 'كلية العلوم الصحية', 1),
            ('ART', 'College of Arts & Humanities', 'كلية الآداب', 1)]:
        with _guard(env, 'college %s' % code):
            ctx.colleges.append(College.create({
                'code': code, 'name_en': en, 'name_ar': ar,
                'institution_id': ctx.institutions[inst_idx % len(ctx.institutions)].id}))
    Dept = env['ums.department']
    for code, en, ar, col_idx in [
            ('CE', 'Civil Engineering', 'الهندسة المدنية', 0),
            ('EE', 'Electrical Engineering', 'الهندسة الكهربائية', 0),
            ('CS', 'Computer Science', 'علوم الحاسب', 1),
            ('IS', 'Information Systems', 'نظم المعلومات', 1),
            ('ACC', 'Accounting', 'المحاسبة', 2),
            ('MKT', 'Marketing', 'التسويق', 2),
            ('MATH', 'Mathematics', 'الرياضيات', 3),
            ('PHYS', 'Physics', 'الفيزياء', 3),
            ('NUR', 'Nursing', 'التمريض', 4),
            ('PH', 'Public Health', 'الصحة العامة', 4),
            ('ENGL', 'English Language', 'اللغة الإنجليزية', 5),
            ('HIST', 'History', 'التاريخ', 5)]:
        with _guard(env, 'department %s' % code):
            ctx.departments.append(Dept.create({
                'code': code, 'name_en': en, 'name_ar': ar,
                'college_id': ctx.colleges[col_idx % len(ctx.colleges)].id}))
    _logger.info("UMS demo: %s colleges, %s departments",
                 len(ctx.colleges), len(ctx.departments))


# ------------------------------------------------------------------ catalog ---
def _catalog(env, ctx):
    Program = env['ums.program']
    Outcome = env['ums.learning.outcome']
    degrees = ['bachelor', 'bachelor', 'bachelor', 'master', 'master', 'phd']
    langs = ['ar', 'en', 'bilingual']
    for i, dept in enumerate(ctx.departments):
        with _guard(env, 'program %s' % dept.code):
            prog = Program.create({
                'code': 'P%s' % dept.code,
                'name_en': 'B.Sc. %s' % dept.name_en,
                'name_ar': 'بكالوريوس %s' % dept.name_ar,
                'department_id': dept.id,
                'degree_type': degrees[i % len(degrees)],
                'duration_years': 4.0, 'total_credit_hours': 24,
                'language': langs[i % len(langs)]})
            ctx.programs.append(prog)
            ctx.plos[prog.id] = [Outcome.create({
                'code': '%s-PLO%s' % (prog.code, k),
                'name': 'Competency area %s for %s.' % (k, prog.name_en),
                'outcome_type': 'plo', 'program_id': prog.id}) for k in range(1, 4)]

    Course = env['ums.course']
    subjects = [('Programming', 'البرمجة'), ('Calculus', 'التفاضل والتكامل'),
                ('Physics', 'الفيزياء'), ('Statistics', 'الإحصاء'),
                ('Databases', 'قواعد البيانات'), ('Networks', 'الشبكات'),
                ('Algorithms', 'الخوارزميات'), ('Accounting', 'المحاسبة'),
                ('Marketing', 'التسويق'), ('Management', 'الإدارة'),
                ('Circuits', 'الدوائر'), ('Mechanics', 'الميكانيكا'),
                ('Chemistry', 'الكيمياء'), ('English', 'الإنجليزية'),
                ('History', 'التاريخ'), ('Ethics', 'الأخلاقيات'),
                ('Anatomy', 'التشريح'), ('Nutrition', 'التغذية'),
                ('Economics', 'الاقتصاد'), ('Finance', 'التمويل')]
    types = ['university', 'college', 'major', 'major', 'elective']
    n = 0
    for level in range(1, 4):
        for s_en, s_ar in subjects:
            if len(ctx.courses) >= 30:
                break
            n += 1
            dept = ctx.departments[n % len(ctx.departments)] if ctx.departments else None
            if not dept:
                break
            with _guard(env, 'course %s' % n):
                ctx.courses.append(Course.create({
                    'code': '%s%s%02d' % (dept.code, level, n),
                    'name_en': '%s %s' % (s_en, level),
                    'name_ar': '%s %s' % (s_ar, level),
                    'department_id': dept.id, 'credit_hours': 3, 'lecture_hours': 3,
                    'lab_hours': 1 if n % 3 == 0 else 0, 'level': level,
                    'course_type': types[n % len(types)]}))
    if len(ctx.courses) >= 30:
        with _guard(env, 'prereq link'):
            env['ums.course.prerequisite'].create({
                'course_id': ctx.courses[29].id,
                'prerequisite_course_id': ctx.courses[28].id})
    _logger.info("UMS demo: %s programs, %s courses", len(ctx.programs), len(ctx.courses))


def _study_plans(env, ctx):
    Plan, Line, Clo = env['ums.study.plan'], env['ums.study.plan.line'], env['ums.learning.outcome']
    if not ctx.courses:
        return
    for pi, prog in enumerate(ctx.programs):
        with _guard(env, 'plan %s' % prog.code):
            plan = Plan.create({'program_id': prog.id, 'version': 1,
                                'effective_term': 'Fall 2026'})
            chosen, seen = [], []
            for k in range(8):
                course = ctx.courses[(pi * 2 + k) % len(ctx.courses)]
                if course in seen:
                    course = ctx.courses[(pi * 2 + k + 8) % len(ctx.courses)]
                seen.append(course)
                chosen.append(course)
            for k, course in enumerate(chosen):
                Line.create({'study_plan_id': plan.id, 'course_id': course.id,
                             'level': (k // 2) + 1, 'semester': str((k % 2) + 1)})
                Clo.create({'code': '%s-%s-CLO' % (prog.code, course.code),
                            'name': 'Apply %s concepts.' % course.name_en,
                            'outcome_type': 'clo', 'course_id': course.id,
                            'mapped_plo_ids': [(4, ctx.plos[prog.id][0].id)]
                            if ctx.plos.get(prog.id) else False})
            plan.action_activate()
            ctx.plans.append(plan)
    with _guard(env, 'grade scheme 4.0'):
        scheme = env['ums.grade.scheme'].create({
            'code': 'US4', 'name_en': 'US 4.0 Scale', 'name_ar': 'سلم 4.0', 'scale': '4'})
        for letter, lo, hi, gp, fail in [('A', 90, 100, 4.0, False), ('B', 80, 89.99, 3.0, False),
                                         ('C', 70, 79.99, 2.0, False), ('D', 60, 69.99, 1.0, False),
                                         ('F', 0, 59.99, 0.0, True)]:
            env['ums.grade.scheme.line'].create({
                'scheme_id': scheme.id, 'letter': letter, 'min_mark': lo,
                'max_mark': hi, 'grade_point': gp, 'is_fail': fail})
    _logger.info("UMS demo: %s study plans", len(ctx.plans))


# ----------------------------------------------------------------- calendar ---
def _calendar(env, ctx):
    Year, Term, Key = env['ums.academic.year'], env['ums.term'], env['ums.key.date']
    for name, code, ds, de, cur in [
            ('2025/2026', 'AY2526', date(2025, 8, 1), date(2026, 7, 31), False),
            ('2026/2027', 'AY2627', date(2026, 8, 1), date(2027, 7, 31), True),
            ('2027/2028', 'AY2728', date(2027, 8, 1), date(2028, 7, 31), False)]:
        with _guard(env, 'year %s' % code):
            ctx.years.append(Year.create({'name': name, 'code': code, 'date_start': ds,
                                          'date_end': de, 'is_current': cur}))
    if not ctx.years:
        return
    for yi, ttype, name, ds, de, state, cur in [
            (0, 'fall', 'Fall 2025', date(2025, 8, 24), date(2025, 12, 31), 'closed', False),
            (0, 'spring', 'Spring 2026', date(2026, 1, 18), date(2026, 5, 31), 'closed', False),
            (0, 'summer', 'Summer 2026', date(2026, 6, 7), date(2026, 8, 6), 'grading', False),
            (1, 'fall', 'Fall 2026', date(2026, 8, 23), date(2026, 12, 31), 'registration', True),
            (1, 'spring', 'Spring 2027', date(2027, 1, 17), date(2027, 5, 31), 'planning', False),
            (1, 'summer', 'Summer 2027', date(2027, 6, 6), date(2027, 8, 5), 'planning', False),
            (2, 'fall', 'Fall 2027', date(2027, 8, 22), date(2027, 12, 31), 'planning', False)]:
        with _guard(env, 'term %s' % name):
            term = Term.create({'name': name, 'code': name.replace(' ', '').upper(),
                                'academic_year_id': ctx.years[yi % len(ctx.years)].id,
                                'term_type': ttype, 'date_start': ds, 'date_end': de,
                                'state': state, 'is_current': cur})
            ctx.terms.append(term)
            if cur:
                ctx.current_term = term
            for nm, dtype, kw in [
                    ('Registration', 'registration', {'date_start': ds - timedelta(days=14), 'date_end': ds + timedelta(days=7)}),
                    ('Add / Drop', 'add_drop', {'date_start': ds, 'date_end': ds + timedelta(days=14)}),
                    ('Withdrawal Deadline', 'withdraw', {'date': ds + timedelta(days=70)}),
                    ('Final Exams', 'exam', {'date_start': de - timedelta(days=14), 'date_end': de - timedelta(days=2)}),
                    ('Results', 'results', {'date': de})]:
                Key.create(dict({'term_id': term.id, 'name': nm, 'date_type': dtype}, **kw))
    Room = env['ums.room']
    rtypes = ['lecture', 'lab', 'seminar', 'exam']
    for i in range(25):
        with _guard(env, 'room %s' % i):
            ctx.rooms.append(Room.create({
                'code': 'R%03d' % (i + 1), 'name': 'Room %s-%s' % (chr(65 + i % 5), 100 + i),
                'building': 'Building %s' % chr(65 + i % 5), 'capacity': 30 + (i % 4) * 10,
                'exam_capacity': 20 + (i % 4) * 5, 'room_type': rtypes[i % 4],
                'gender': 'mixed' if i % 3 else ('male' if i % 2 else 'female')}))
    Slot = env['ums.timeslot']
    for d in ['6', '0', '1', '2', '3']:
        for hf, ht in [(8, 10), (10, 12), (12, 14), (14, 16), (16, 18), (18, 20)]:
            with _guard(env, 'slot'):
                ctx.slots.append(Slot.create({'dayofweek': d, 'hour_from': float(hf),
                                              'hour_to': float(ht)}))
    _logger.info("UMS demo: %s terms, %s rooms, %s slots",
                 len(ctx.terms), len(ctx.rooms), len(ctx.slots))


# ------------------------------------------------------------------- people ---
def _people(env, ctx):
    Users = env['res.users']
    base_user = env.ref('base.group_user', raise_if_not_found=False)
    faculty_group = env.ref('ums_lms.ums_group_faculty', raise_if_not_found=False)
    group_cmds = [(4, g.id) for g in (base_user, faculty_group) if g]
    for i in range(12):
        with _guard(env, 'instructor %s' % i):
            vals = {'name': 'Dr. %s' % _name(i), 'login': 'ums_demo_instr_%s' % (i + 1),
                    'email': 'instr%s@demo.ums' % (i + 1)}
            if group_cmds:
                vals['groups_id'] = group_cmds
            ctx.instructors.append(Users.create(vals))
    Emp = env['hr.employee']
    ranks = ['lecturer', 'assistant', 'associate', 'professor']
    for i in range(12):
        with _guard(env, 'faculty %s' % i):
            user = ctx.instructors[i] if i < len(ctx.instructors) else False
            dept = ctx.departments[i % len(ctx.departments)] if ctx.departments else False
            ctx.faculty.append(Emp.create({
                'name': user.name if user else 'Faculty %s' % i, 'is_faculty': True,
                'academic_rank': ranks[i % 4],
                'specialisation': dept.name_en if dept else False,
                'ums_department_id': dept.id if dept else False,
                'max_teaching_load': 12, 'user_id': user.id if user else False}))
    _logger.info("UMS demo: %s instructors, %s faculty", len(ctx.instructors), len(ctx.faculty))


def _sections(env, ctx):
    if not (ctx.current_term and ctx.courses and ctx.slots and ctx.rooms):
        return
    Section, Exam = env['ums.section'], env['ums.exam.schedule']
    for i in range(min(25, len(ctx.courses))):
        with _guard(env, 'section %s' % i):
            ctx.sections.append(Section.create({
                'course_id': ctx.courses[i].id, 'term_id': ctx.current_term.id,
                'code': '%02d' % (1 + i % 3),
                'instructor_id': ctx.instructors[i % len(ctx.instructors)].id if ctx.instructors else False,
                'room_id': ctx.rooms[i % len(ctx.rooms)].id,
                'timeslot_ids': [(6, 0, [ctx.slots[i % len(ctx.slots)].id])],
                'capacity': 50, 'gender': 'mixed', 'state': 'open'}))
    base = ctx.current_term.date_end - timedelta(days=14)
    for i, sec in enumerate(ctx.sections):
        with _guard(env, 'exam %s' % i):
            Exam.create({'section_id': sec.id, 'exam_type': 'final',
                         'exam_date': base + timedelta(days=i % 10),
                         'hour_from': 9.0 if i % 2 == 0 else 13.0,
                         'hour_to': 11.0 if i % 2 == 0 else 15.0,
                         'room_id': ctx.rooms[i % len(ctx.rooms)].id, 'state': 'draft'})
    _logger.info("UMS demo: %s sections", len(ctx.sections))


# ----------------------------------------------------------------- students ---
def _students(env, ctx):
    if not ctx.programs:
        return
    Student = env['ums.student']
    for i in range(25):
        with _guard(env, 'student %s' % i):
            prog = ctx.programs[i % len(ctx.programs)]
            plan = next((p for p in ctx.plans
                         if p.program_id == prog and p.state == 'active'), False)
            advisor = ctx.instructors[i % len(ctx.instructors)] if ctx.instructors else False
            ctx.students.append(Student.create({
                'name': _name(i), 'national_id': '1%09d' % (1000 + i),
                'email': 'student%s@demo.ums' % (i + 1), 'phone': '+96650%07d' % (1000000 + i),
                'program_id': prog.id, 'study_plan_id': plan.id if plan else False,
                'advisor_id': advisor.id if advisor else False,
                'admission_term_id': ctx.current_term.id if ctx.current_term else False,
                'level': 1 + (i % 4), 'gender': 'male' if i % 2 == 0 else 'female',
                'student_type': ['regular', 'transfer', 'international', 'sponsored'][i % 4],
                'status': 'active'}))
    _logger.info("UMS demo: %s students", len(ctx.students))


def _registrations_and_grades(env, ctx):
    if not (ctx.students and ctx.sections):
        return
    Reg, Entry = env['ums.registration'], env['ums.grade.entry']
    n = len(ctx.sections)
    for i, student in enumerate(ctx.students):
        with _guard(env, 'registrations %s' % i):
            regs = []
            for k in range(5):
                regs.append(Reg.create({'student_id': student.id,
                                        'section_id': ctx.sections[(i + k) % n].id,
                                        'state': 'registered'}))
            for j, reg in enumerate(regs[:3]):
                mark = 95 - ((i + j) % 4) * 7
                if (i % 9) == 0 and j == 0:
                    mark = 48
                entry = Entry.create({'registration_id': reg.id, 'total_mark': mark})
                entry.action_submit()
                entry.action_approve()
    _logger.info("UMS demo: registrations and grades created")


def _holds_and_advising(env, ctx):
    if not ctx.students:
        return
    Hold, Note = env['ums.hold'], env['ums.advising.note']
    htypes = ['financial', 'academic', 'disciplinary', 'library', 'admin']
    subjects = ['Course selection', 'Probation review', 'Career guidance',
                'Internship advice', 'Graduation plan']
    for i, student in enumerate(ctx.students):
        with _guard(env, 'hold %s' % i):
            Hold.create({'student_id': student.id, 'hold_type': htypes[i % len(htypes)],
                         'reason': 'Demo %s hold' % htypes[i % len(htypes)],
                         'blocks_registration': False, 'blocks_transcript': i % 4 == 0,
                         'active': i % 3 != 0})
        with _guard(env, 'advising %s' % i):
            Note.create({'student_id': student.id,
                         'advisor_id': student.advisor_id.id or env.uid,
                         'note_date': date(2026, 6, 1) + timedelta(days=i % 15),
                         'subject': subjects[i % len(subjects)],
                         'note': 'Met with the student about %s.'
                         % subjects[i % len(subjects)].lower()})
    _logger.info("UMS demo: holds and advising notes created")


# --------------------------------------------------------------- admissions ---
def _admissions(env, ctx):
    if not (ctx.terms and ctx.programs):
        return
    Intake, Quota = env['ums.intake'], env['ums.seat.quota']
    intake_terms = [t for t in ctx.terms if t.state in ('registration', 'planning')][:4] \
        or ctx.terms[:4]
    for i, term in enumerate(intake_terms):
        with _guard(env, 'intake %s' % i):
            intake = Intake.create({
                'name': '%s Intake' % term.name, 'code': 'IN%s' % (i + 1),
                'term_id': term.id, 'date_open': term.date_start - timedelta(days=120),
                'date_close': term.date_start - timedelta(days=10),
                'application_fee': 250.0, 'state': 'open' if i == 0 else 'draft'})
            ctx.intakes.append(intake)
            if i == 0:
                ctx.current_intake = intake
            for prog in ctx.programs[:6]:
                Quota.create({'intake_id': intake.id, 'program_id': prog.id,
                              'gender': 'any', 'seats': 50})
    Lead = env['ums.lead']
    sources = ['website', 'phone', 'email', 'walk_in', 'event', 'social', 'referral']
    stages = ['new', 'contacted', 'qualified', 'applied', 'lost']
    for i in range(25):
        with _guard(env, 'lead %s' % i):
            Lead.create({'name': _name(i, 3), 'email': 'lead%s@prospect.ums' % (i + 1),
                         'phone': '+96655%07d' % (2000000 + i),
                         'program_id': ctx.programs[i % len(ctx.programs)].id,
                         'intake_id': ctx.current_intake.id if ctx.current_intake else False,
                         'source': sources[i % len(sources)], 'stage': stages[i % len(stages)]})
    App, Doc = env['ums.application'], env['ums.application.document']
    states = ['draft', 'submitted', 'under_review', 'shortlisted', 'offer',
              'accepted', 'waitlisted', 'rejected']
    default_intake = ctx.current_intake or (ctx.intakes[0] if ctx.intakes else None)
    for i in range(25):
        with _guard(env, 'application %s' % i):
            app = App.create({
                'partner_name': _name(i, 5), 'national_id': '2%09d' % (3000 + i),
                'email': 'applicant%s@demo.ums' % (i + 1),
                'gender': 'male' if i % 2 else 'female',
                'program_id': ctx.programs[i % len(ctx.programs)].id,
                'intake_id': default_intake.id if default_intake else False,
                'qiyas_score': 70 + (i % 25), 'tahsili_score': 65 + (i % 30),
                'hs_gpa': 80 + (i % 18), 'fee_paid': i % 3 != 0,
                'state': states[i % len(states)]})
            for dt in ('national_id', 'hs_certificate', 'transcript'):
                Doc.create({'application_id': app.id, 'doc_type': dt,
                            'name': dt.replace('_', ' ').title(), 'required': True,
                            'state': 'verified' if i % 2 else 'pending'})
    _logger.info("UMS demo: admissions created")


# ----------------------------------------------------------------- teaching ---
def _teaching(env, ctx):
    Rubric, Crit = env['ums.rubric'], env['ums.rubric.criterion']
    for i in range(8):
        with _guard(env, 'rubric %s' % i):
            r = Rubric.create({'name': 'Rubric %s' % (i + 1)})
            for cn, mp in [('Content', 50), ('Structure', 30), ('Presentation', 20)]:
                Crit.create({'rubric_id': r.id, 'name': cn, 'max_points': mp})
    if ctx.sections:
        Assign, Sub = env['ums.assignment'], env['ums.assignment.submission']
        for i, sec in enumerate(ctx.sections):
            with _guard(env, 'assignment %s' % i):
                assignment = Assign.create({
                    'name': 'Assignment %s — %s' % (i + 1, sec.course_id.name_en),
                    'section_id': sec.id, 'max_score': 100, 'weight': 20,
                    'due_date': datetime(2026, 11, 1, 23, 59) + timedelta(days=i % 20),
                    'state': 'published'})
                for reg in sec.registration_ids[:6]:
                    Sub.create({'assignment_id': assignment.id,
                                'student_id': reg.student_id.id,
                                'submitted_date': datetime(2026, 10, 28, 12, 0),
                                'score': 70 + (reg.id % 30), 'state': 'graded'})
        Sess = env['ums.attendance.session']
        for i, sec in enumerate(ctx.sections):
            with _guard(env, 'attendance %s' % i):
                session = Sess.create({'section_id': sec.id,
                                       'session_date': date(2026, 9, 1) + timedelta(days=i),
                                       'hour_from': 8.0, 'hour_to': 10.0})
                session.action_load_roster()
                for j, line in enumerate(session.line_ids):
                    if j % 5 == 0:
                        line.status = 'absent'
                session.action_mark_done()
    Link = env['ums.lms.link']
    for i, (lt, std) in enumerate([('moodle', 'lti13'), ('canvas', 'lti13'),
                                   ('blackboard', 'oneroster'), ('odoo_elearning', 'scorm'),
                                   ('moodle', 'xapi')]):
        with _guard(env, 'lms link %s' % i):
            Link.create({'name': '%s Connector' % lt.title(), 'lms_type': lt,
                         'standard': std, 'base_url': 'https://lms%s.demo.ums' % (i + 1)})
    _logger.info("UMS demo: teaching data created")


def _assessment_config(env, ctx):
    if not ctx.sections:
        return
    Comp = env['ums.assessment.component']
    for sec in ctx.sections:
        with _guard(env, 'components %s' % sec.id):
            for name, ctype, weight in [('Quizzes', 'quiz', 20), ('Midterm', 'midterm', 30),
                                        ('Final Exam', 'final', 50)]:
                Comp.create({'section_id': sec.id, 'name': name, 'component_type': ctype,
                             'weight': weight, 'max_mark': 100})
    _logger.info("UMS demo: assessment components created")


# ------------------------------------------------------------------ finance ---
def _finance(env, ctx):
    Fee, Item = env['ums.fee.structure'], env['ums.fee.item']
    stypes = ['regular', 'transfer', 'international', 'sponsored']
    for i, prog in enumerate(ctx.programs):
        for st in {stypes[i % 4], 'regular'}:
            with _guard(env, 'fee %s/%s' % (prog.code, st)):
                fee = Fee.create({'name': '%s — %s' % (prog.name_en, st.title()),
                                  'program_id': prog.id, 'level': 0, 'student_type': st,
                                  'per_ch_rate': 400 + (i % 5) * 50})
                Item.create({'structure_id': fee.id, 'name': 'Registration Fee',
                             'amount': 200, 'is_vat_exempt': True})
                Item.create({'structure_id': fee.id, 'name': 'Student Services',
                             'amount': 150, 'is_vat_exempt': False})
    _logger.info("UMS demo: fee structures created")


def _faculty_load(env, ctx):
    if not (ctx.faculty and ctx.current_term and ctx.sections):
        return
    Load = env['ums.teaching.load']
    for i, emp in enumerate(ctx.faculty):
        with _guard(env, 'load %s' % i):
            secs = [s for s in ctx.sections if s.instructor_id and s.instructor_id == emp.user_id][:3]
            if not secs:
                secs = ctx.sections[i % len(ctx.sections):][:2]
            Load.create({'employee_id': emp.id, 'term_id': ctx.current_term.id,
                         'section_ids': [(6, 0, [s.id for s in secs])]})
    _logger.info("UMS demo: teaching loads created")


# --------------------------------------------------- graduation, credentials ---
def _graduation(env, ctx):
    if not (ctx.students and ctx.current_term):
        return
    Grad = env['ums.graduation']
    states = ['draft', 'eligible', 'cleared', 'graduated']
    classes = ['Excellent (Mumtaz)', 'Very Good (Jayyid Jiddan)', 'Good (Jayyid)']
    for i, student in enumerate(ctx.students[:15]):
        with _guard(env, 'graduation %s' % i):
            Grad.create({'student_id': student.id, 'term_id': ctx.current_term.id,
                         'final_cgpa': round(3.5 + (i % 15) * 0.1, 2),
                         'classification': classes[i % len(classes)],
                         'graduation_date': date(2026, 12, 31) if i % 4 == 3 else False,
                         'state': states[i % len(states)]})
    _logger.info("UMS demo: graduations created")


def _credentials(env, ctx):
    if not ctx.students:
        return
    Cred = env['ums.credential']
    ctypes = ['degree', 'badge', 'course', 'award']
    for i, student in enumerate(ctx.students):
        with _guard(env, 'credential %s' % i):
            cred = Cred.create({
                'name': '%s — %s' % (ctypes[i % 4].title(), student.program_id.name_en),
                'credential_type': ctypes[i % 4], 'student_id': student.id,
                'program_id': student.program_id.id,
                'issue_date': date(2026, 6, 1) + timedelta(days=i % 20)})
            if i % 3 != 0:
                cred.action_issue()
    _logger.info("UMS demo: credentials created")


# -------------------------------------------- analytics, accreditation, lxp ---
def _analytics(env, ctx):
    Kpi = env['ums.kpi']
    for prog in ctx.programs:
        with _guard(env, 'kpi %s' % prog.code):
            Kpi.snapshot(prog)
    _logger.info("UMS demo: KPI snapshots created")


def _accreditation(env, ctx):
    Report = env['ums.accreditation.report']
    rtypes = ['program', 'course', 'kpi_pack', 'self_study']
    states = ['draft', 'submitted', 'approved']
    for i, prog in enumerate(ctx.programs):
        for k in range(2):
            with _guard(env, 'accreditation %s/%s' % (i, k)):
                Report.create({
                    'name': '%s %s Report 2026' % (prog.name_en, rtypes[(i + k) % 4].title()),
                    'program_id': prog.id, 'report_type': rtypes[(i + k) % 4],
                    'period': 'AY 2026/2027', 'state': states[(i + k) % 3]})
    _logger.info("UMS demo: accreditation reports created")


def _pathways(env, ctx):
    Path, Step = env['ums.pathway'], env['ums.pathway.step']
    for i, prog in enumerate(ctx.programs):
        for lvl in (1, 2):
            with _guard(env, 'pathway %s/%s' % (i, lvl)):
                p = Path.create({'name': '%s — Level %s Pathway' % (prog.name_en, lvl),
                                 'description': 'Curated journey for %s.' % prog.name_en,
                                 'program_id': prog.id, 'level': lvl})
                for s in range(3):
                    course = ctx.courses[(i + lvl + s) % len(ctx.courses)] if ctx.courses else False
                    Step.create({'pathway_id': p.id, 'name': 'Step %s' % (s + 1),
                                 'course_id': course.id if course else False,
                                 'content_url': 'https://lxp.demo.ums/p%s/s%s' % (i, s),
                                 'estimated_hours': 4.0 + s})
    _logger.info("UMS demo: pathways created")


def _pdpl_and_audit(env, ctx):
    Consent, Request = env['ums.consent'], env['ums.data.request']
    bases = ['consent', 'contract', 'legal', 'legitimate']
    purposes = ['Admissions processing', 'Academic records', 'Financial billing',
                'Marketing communications', 'Alumni engagement']
    rtypes = ['access', 'correction', 'erasure', 'objection', 'portability']
    for i, student in enumerate(ctx.students):
        with _guard(env, 'consent %s' % i):
            Consent.create({'partner_id': student.partner_id.id,
                            'purpose': purposes[i % len(purposes)],
                            'lawful_basis': bases[i % len(bases)],
                            'consent_date': date(2026, 1, 1) + timedelta(days=i),
                            'state': 'given' if i % 4 else 'withdrawn'})
        with _guard(env, 'data request %s' % i):
            Request.create({'partner_id': student.partner_id.id,
                            'request_type': rtypes[i % len(rtypes)],
                            'description': 'Demo PDPL %s request.' % rtypes[i % len(rtypes)],
                            'state': ['submitted', 'in_review', 'completed', 'rejected'][i % 4]})
    Audit = env['ums.audit.log']
    cats = ['grade', 'finance', 'admission', 'config', 'access', 'data']
    for i in range(25):
        with _guard(env, 'audit %s' % i):
            Audit.log_action('Demo action %s' % (i + 1), cats[i % len(cats)],
                             description='Demonstration audit entry %s.' % (i + 1))
    _logger.info("UMS demo: PDPL and audit entries created")
