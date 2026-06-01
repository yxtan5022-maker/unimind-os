use crate::lib_unibit::{UnibitConfig, UnibitEngine};

#[no_mangle]
pub extern "C" fn umos_fold_bits(
    bits_ptr: *const u8,
    bits_len: usize,
    out_len: *mut usize,
) -> *mut f64 {
    if bits_ptr.is_null() || out_len.is_null() {
        return std::ptr::null_mut();
    }

    let bits = unsafe { std::slice::from_raw_parts(bits_ptr, bits_len) };
    let engine = UnibitEngine::new(UnibitConfig::default());
    let mut out = engine.fold_bits(bits);
    let ptr = out.as_mut_ptr();
    unsafe {
        *out_len = out.len();
    }
    std::mem::forget(out);
    ptr
}

#[no_mangle]
pub extern "C" fn umos_collapse_signal(
    signal_ptr: *const f64,
    signal_len: usize,
    threshold: f64,
    out_len: *mut usize,
) -> *mut u8 {
    if signal_ptr.is_null() || out_len.is_null() {
        return std::ptr::null_mut();
    }

    let signal = unsafe { std::slice::from_raw_parts(signal_ptr, signal_len) };
    let mut cfg = UnibitConfig::default();
    cfg.collapse_threshold = threshold;
    let engine = UnibitEngine::new(cfg);
    let mut out = engine.collapse_signal(signal);
    let ptr = out.as_mut_ptr();
    unsafe {
        *out_len = out.len();
    }
    std::mem::forget(out);
    ptr
}

#[no_mangle]
pub extern "C" fn umos_free_f64(ptr: *mut f64, len: usize) {
    if ptr.is_null() {
        return;
    }
    unsafe {
        drop(Vec::from_raw_parts(ptr, len, len));
    }
}

#[no_mangle]
pub extern "C" fn umos_free_u8(ptr: *mut u8, len: usize) {
    if ptr.is_null() {
        return;
    }
    unsafe {
        drop(Vec::from_raw_parts(ptr, len, len));
    }
}

