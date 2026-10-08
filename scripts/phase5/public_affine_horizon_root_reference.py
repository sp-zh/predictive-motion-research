"""Independent general-affine algebra oracle; definitions only.

Normalized cells mean x[c+1] = A[c] x[c] + B[c] u[c] + d[c].
Normalized samples mean x[p] = A[p] x[cell] + B[p] u[cell] + d[p],
where their A/B/d are WHOLE-CELL prefixes, not last-cycle local fields.
The actual-coordinate lifted order is y = [x[0], ..., x[N], u[0], ..., u[N-1]].

The primary reference solves a separately assembled lifted system with partial
pivoting. A separate recurrence is available for comparison. No producer
verifier is imported. This module contains no top-level evaluation or model,
binary, fitting, plant, build, solver-optimization or controller calls.
Algebra equality proves no admissibility, branch segment/ball, finite trust
radius, physical accuracy or Phase5 gate; the retained boundary FD failure is
not reversed. Input identities/policy/fixtures must freeze before evaluations.
"""
import numbers

import numpy as np


def _integer(value, name, minimum=1):
    if type(value) is not int or value < minimum:
        raise ValueError(name + ' must be a typed integer >= ' + str(minimum))
    return value


def _real(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
        raise ValueError(name + ' must be real, not bool/string/complex')
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(name + ' cannot be represented as float64') from error
    if not np.isfinite(result):
        raise ValueError(name + ' must be finite')
    return result


def _array(value, shape, name):
    def leaves(item):
        if isinstance(item, np.ndarray):
            return leaves(item.tolist())
        if isinstance(item, (list, tuple)):
            for entry in item:
                leaves(entry)
        else:
            _real(item, name)
    if not isinstance(value, (list, tuple, np.ndarray)):
        raise ValueError(name + ' must be an array')
    leaves(value)
    try:
        result = np.array(value, dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(name + ' must be a rectangular numeric array') from error
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(name + ' must have finite shape ' + str(shape))
    return result


def _finite(value, name):
    if not np.isfinite(value).all():
        raise FloatingPointError(name + ' arithmetic is nonfinite')
    return value


def _mul(left, right, name):
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        return _finite(left @ right, name)


def _add(left, right, name):
    with np.errstate(over='raise', invalid='raise'):
        return _finite(left + right, name)


def _sub(left, right, name):
    with np.errstate(over='raise', invalid='raise'):
        return _finite(left - right, name)


def _scaled(value, scale, name):
    with np.errstate(over='raise', invalid='raise'):
        return _finite(value * scale, name)


def _normalized(nx, nu, initial, cells, samples):
    _integer(nx, 'nx'); _integer(nu, 'nu')
    x0 = _array(initial, (nx,), 'actual initial')
    if not isinstance(cells, (list, tuple)) or not cells:
        raise ValueError('nonempty normalized cell sequence required')
    normalized = []
    for index, cell in enumerate(cells):
        if type(cell) is not dict:
            raise ValueError('cell must be a normalized dictionary')
        normalized.append(dict(A=_array(cell['A'], (nx, nx), 'cell A '+str(index)),
                               B=_array(cell['B'], (nx, nu), 'cell B '+str(index)),
                               d=_array(cell['d'], (nx,), 'cell d '+str(index))))
    if not isinstance(samples, (list, tuple)):
        raise ValueError('normalized sample sequence required')
    prefixes = []
    for index, sample in enumerate(samples):
        if type(sample) is not dict:
            raise ValueError('sample must be a normalized dictionary')
        cell = _integer(sample['cell'], 'sample cell', 0)
        if cell >= len(normalized):
            raise ValueError('sample cell outside normalized roster')
        prefixes.append(dict(cell=cell, A=_array(sample['A'], (nx, nx), 'sample A '+str(index)),
                             B=_array(sample['B'], (nx, nu), 'sample B '+str(index)),
                             d=_array(sample['d'], (nx,), 'sample d '+str(index))))
    return x0, normalized, prefixes


def pivoted_solve(matrix, rhs):
    """Independent partial-pivot Gaussian elimination with multiple RHS.

    No forward cell recurrence or np.linalg.solve is used. Zero pivots reject;
    the caller may impose preregistered residual/conditioning gates separately.
    """
    raw = np.asarray(matrix)
    if raw.ndim != 2 or raw.shape[0] == 0 or raw.shape[0] != raw.shape[1]:
        raise ValueError('square nonempty pivoted system')
    size = raw.shape[0]; a = _array(matrix, (size, size), 'pivoted matrix')
    raw_rhs = np.asarray(rhs)
    if raw_rhs.ndim != 2 or raw_rhs.shape[0] != size:
        raise ValueError('pivoted RHS must be a matrix with matching rows')
    b = _array(rhs, raw_rhs.shape, 'pivoted RHS')
    for column in range(size):
        pivot = column + int(np.argmax(np.abs(a[column:, column])))
        if a[pivot, column] == 0:
            raise ValueError('singular pivoted system')
        if pivot != column:
            a[[column, pivot]] = a[[pivot, column]]
            b[[column, pivot]] = b[[pivot, column]]
        for row in range(column+1, size):
            with np.errstate(over='raise', invalid='raise', divide='raise'):
                multiplier = _finite(a[row, column] / a[column, column], 'pivot ratio')
            a[row, column+1:] = _sub(a[row, column+1:],
                _scaled(a[column, column+1:], multiplier, 'elimination matrix product'), 'elimination matrix')
            b[row] = _sub(b[row], _scaled(b[column], multiplier, 'elimination RHS product'), 'elimination RHS')
            a[row, column] = 0.
    solution = np.zeros_like(b)
    for row in range(size-1, -1, -1):
        tail = _mul(a[row, row+1:], solution[row+1:], 'back substitution product')
        numerator = _sub(b[row], tail, 'back substitution numerator')
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            solution[row] = _finite(numerator / a[row, row], 'back substitution division')
    return _finite(solution, 'pivoted solution')


def _outputs(nx, nu, cells, prefixes, offsets, controls, initials):
    count = len(cells); nc = count*nu; ns = (count+1)*nx
    sample_outputs = []
    for sample in prefixes:
        cell = sample['cell']; A, B, d = sample['A'], sample['B'], sample['d']
        selector = np.zeros((nu, nc)); selector[:, cell*nu:(cell+1)*nu] = np.eye(nu)
        offset = _add(_mul(A, offsets[cell], 'sample offset product'), d, 'sample offset')
        control = _add(_mul(A, controls[cell], 'sample control product'),
                       _mul(B, selector, 'sample selected control'), 'sample control map')
        initial = _mul(A, initials[cell], 'sample initial map')
        # Sample expression in ACTUAL lifted coordinates [X,U].
        lifted = np.zeros((nx, ns+nc)); lifted[:, cell*nx:(cell+1)*nx] = A
        lifted[:, ns+cell*nu:ns+(cell+1)*nu] = B
        sample_outputs.append(dict(cell=cell, offset=offset, control_map=control, initial_map=initial,
                                   lifted_map=lifted, lifted_offset=d.copy()))
    state_control = controls.reshape(ns, nc); state_initial = initials.reshape(ns, nx)
    embedding = np.vstack((state_control, np.eye(nc)))
    offset = np.r_[offsets.reshape(ns), np.zeros(nc)]
    initial_embedding = np.vstack((state_initial, np.zeros((nc, nx))))
    for name, result in (('lifted embedding', embedding), ('lifted offset', offset),
                         ('lifted initial embedding', initial_embedding)):
        _finite(result, name)
    return dict(nx=nx, nu=nu, cell_count=count, state_offsets=offsets, state_control_maps=controls,
                state_initial_maps=initials, samples=sample_outputs, embedding_map=embedding,
                embedding_offset=offset, embedding_initial_map=initial_embedding)


def lifted_reference(nx, nu, actual_initial, cells, samples=()):
    """Primary independent L solve, including arbitrary initial injection P.

    L X = E U + f; f=[actual_initial,d0,...], G injects initial perturbations.
    All outputs are actual coordinates. Cell inputs are distinct block columns.
    """
    x0, cells, prefixes = _normalized(nx, nu, actual_initial, cells, samples)
    count = len(cells); ns = (count+1)*nx; nc = count*nu
    L = np.eye(ns); E = np.zeros((ns, nc)); f = np.zeros(ns); G = np.zeros((ns, nx))
    f[:nx] = x0; G[:nx] = np.eye(nx)
    for cell, item in enumerate(cells):
        rows = slice((cell+1)*nx, (cell+2)*nx)
        L[rows, cell*nx:(cell+1)*nx] = -item['A']
        E[rows, cell*nu:(cell+1)*nu] = item['B']; f[rows] = item['d']
    rhs = np.column_stack((E, f, G)); solution = pivoted_solve(L, rhs)
    controls = solution[:, :nc].reshape(count+1, nx, nc)
    offsets = solution[:, nc].reshape(count+1, nx)
    initials = solution[:, nc+1:].reshape(count+1, nx, nx)
    result = _outputs(nx, nu, cells, prefixes, offsets, controls, initials)
    residual = _sub(_mul(L, solution, 'lifted solve residual product'), rhs, 'lifted solve residual')
    result.update(L=L, E=E, f=f, initial_injection=G, solve_residual=residual)
    return result


def recurrence_reference(nx, nu, actual_initial, cells, samples=()):
    """Separate recurrence checker; deliberately not the primary L oracle."""
    x0, cells, prefixes = _normalized(nx, nu, actual_initial, cells, samples)
    count = len(cells); nc = count*nu
    offsets = np.zeros((count+1, nx)); controls = np.zeros((count+1, nx, nc))
    initials = np.zeros((count+1, nx, nx)); offsets[0] = x0; initials[0] = np.eye(nx)
    for cell, item in enumerate(cells):
        offsets[cell+1] = _add(_mul(item['A'], offsets[cell], 'recurrence offset product'), item['d'], 'recurrence offset')
        controls[cell+1] = _mul(item['A'], controls[cell], 'recurrence control product')
        block = slice(cell*nu, (cell+1)*nu)
        controls[cell+1, :, block] = _add(controls[cell+1, :, block], item['B'], 'recurrence selected control')
        initials[cell+1] = _mul(item['A'], initials[cell], 'recurrence initial product')
    return _outputs(nx, nu, cells, prefixes, offsets, controls, initials)


def evaluate_affine(offset, control_map, controls, initial_map=None, initial_shift=None):
    """Value of a frozen affine model, not a nonlinear/plant prediction."""
    raw = np.asarray(offset)
    if raw.ndim != 1:
        raise ValueError('affine offset vector required')
    m = raw.size; o = _array(offset, (m,), 'affine offset'); raw_map = np.asarray(control_map)
    if raw_map.ndim != 2 or raw_map.shape[0] != m:
        raise ValueError('affine control map row shape')
    M = _array(control_map, raw_map.shape, 'affine control map'); u = _array(controls, (M.shape[1],), 'affine controls')
    value = _add(o, _mul(M, u, 'affine control product'), 'affine value')
    if (initial_map is None) != (initial_shift is None):
        raise ValueError('initial map and shift must both be supplied or both absent')
    if initial_map is not None:
        raw_P = np.asarray(initial_map)
        if raw_P.ndim != 2 or raw_P.shape[0] != m:
            raise ValueError('affine initial map row shape')
        P = _array(initial_map, raw_P.shape, 'affine initial map')
        delta = _array(initial_shift, (P.shape[1],), 'actual initial shift')
        value = _add(value, _mul(P, delta, 'affine initial product'), 'shifted affine value')
    return value


def substitute_objective(full_factor, residual_offset, linear, constant,
                         embedding_offset, embedding_map):
    """Substitute y=e+T U into .5||R y+c||^2 + ell'y + k.

    R is arbitrary rectangular, including dense crosscomponent/crosscell rows.
    A zero-row factor is supported if supplied as an explicit (0,ny) array.
    No factor-two or constant omission; output is .5 U'H U + g'U + constant.
    """
    raw_e = np.asarray(embedding_offset); raw_T = np.asarray(embedding_map); raw_R = np.asarray(full_factor)
    if raw_e.ndim != 1 or raw_T.ndim != 2 or raw_T.shape[0] != raw_e.size or raw_R.ndim != 2 or raw_R.shape[1] != raw_e.size:
        raise ValueError('objective embedding/factor shapes')
    ny, nc, rows = raw_e.size, raw_T.shape[1], raw_R.shape[0]
    e = _array(embedding_offset, (ny,), 'actual embedding offset')
    T = _array(embedding_map, (ny, nc), 'actual embedding map')
    R = _array(full_factor, (rows, ny), 'full rectangular factor')
    c = _array(residual_offset, (rows,), 'full residual offset')
    ell = _array(linear, (ny,), 'full linear objective'); k = _real(constant, 'full objective constant')
    factor = _mul(R, T, 'condensed rectangular factor')
    offset = _add(_mul(R, e, 'full factor offset product'), c, 'condensed residual offset')
    H = _mul(factor.T, factor, 'condensed Hessian')
    g = _add(_mul(factor.T, offset, 'factor linear product'), _mul(T.T, ell, 'full linear embedding'), 'condensed gradient')
    square = _scaled(_mul(offset, offset, 'offset square'), .5, 'half offset square')
    shifted_linear = _mul(ell, e, 'linear constant shift')
    cost_constant = _add(_add(square, shifted_linear, 'quadratic/linear constant'), k, 'full constant')
    return dict(H=H, g=g, constant=float(cost_constant), factor=factor, offset=offset,
                linear=_mul(T.T, ell, 'condensed separate linear'),
                full_factor=R, full_offset=c, full_linear=ell, full_constant=k)


def direct_objective(full_factor, residual_offset, linear, constant, actual_lifted):
    """Literal full-coordinate value and gradient, before elimination."""
    raw = np.asarray(actual_lifted); raw_R = np.asarray(full_factor)
    if raw.ndim != 1 or raw_R.ndim != 2 or raw_R.shape[1] != raw.size:
        raise ValueError('direct full objective shape')
    ny, rows = raw.size, raw_R.shape[0]
    y = _array(actual_lifted, (ny,), 'actual lifted vector'); R = _array(full_factor, (rows, ny), 'full factor')
    c = _array(residual_offset, (rows,), 'residual offset'); ell = _array(linear, (ny,), 'linear objective')
    k = _real(constant, 'constant'); residual = _add(_mul(R, y, 'direct factor product'), c, 'direct residual')
    value = _add(_add(_scaled(_mul(residual, residual, 'direct norm square'), .5, 'direct half norm'),
                     _mul(ell, y, 'direct linear value'), 'direct quadratic/linear value'), k, 'direct constant')
    gradient = _add(_mul(R.T, residual, 'direct full gradient product'), ell, 'direct full gradient')
    return dict(value=float(value), gradient=gradient, residual=residual)


def quadratic_objective(H, g, constant, controls):
    """Condensed value/gradient; H must be symmetric within declared tolerance.

    This evaluator rejects asymmetry above 1e-12 absolute; it never repairs H.
    The supplied H is used literally, with gradient .5(H+H.T)U+g.
    """
    raw = np.asarray(controls)
    if raw.ndim != 1:
        raise ValueError('quadratic control vector shape')
    n = raw.size; u = _array(controls, (n,), 'quadratic controls')
    h = _array(H, (n, n), 'quadratic Hessian'); gradient = _array(g, (n,), 'quadratic gradient')
    k = _real(constant, 'quadratic constant')
    difference = _sub(h, h.T, 'H symmetry difference')
    if float(np.max(np.abs(difference), initial=0.)) > 1e-12:
        raise ValueError('literal quadratic Hessian asymmetric')
    hu = _mul(h, u, 'quadratic H times controls')
    value = _add(_add(_scaled(_mul(u, hu, 'quadratic bilinear'), .5, 'quadratic half value'),
                     _mul(gradient, u, 'quadratic linear value'), 'quadratic sum'), k, 'quadratic constant')
    symmetric = _scaled(_add(h, h.T, 'quadratic derivative symmetry'), .5, 'quadratic derivative half')
    derivative = _add(_mul(symmetric, u, 'quadratic gradient product'), gradient, 'quadratic derivative')
    return dict(value=float(value), gradient=derivative)
