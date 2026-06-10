#define QISKIT_C_PYTHON_INTERFACE
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <capnp/message.h>
#include <capnp/serialize-packed.h>
#include <kj/io.h>
#include "qiskit_jeff.h"
#include <qiskit.h>

using namespace jeff::qiskit_convert;

static PyObject* py_jeff_to_qiskit(PyObject* self, PyObject* args) {
    const char* buffer;
    Py_ssize_t length;

    if (!PyArg_ParseTuple(args, "y#", &buffer, &length)) {
        return NULL;
    }

    try {
        auto array = kj::arrayPtr(reinterpret_cast<const capnp::word*>(buffer), length / sizeof(capnp::word));
        ::capnp::FlatArrayMessageReader message(array);
        auto module = message.getRoot<Module>();

        QkCircuit* qc = jeff_to_qiskit(module);
        
        // qk_circuit_to_python_full converts QkCircuit to a Python QuantumCircuit object
        // qk_circuit_to_python converts QkCircuit to a Python CircuitData object
        // We use qk_circuit_to_python_full because the user will want a QuantumCircuit.
        PyObject* py_qc = qk_circuit_to_python_full(qc);
        
        return py_qc;
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return NULL;
    }
}

static PyObject* py_qiskit_to_jeff(PyObject* self, PyObject* args) {
    PyObject* py_circuit = NULL;

    if (!PyArg_ParseTuple(args, "O", &py_circuit)) {
        return NULL;
    }

    // Attempt to borrow QkCircuit from QuantumCircuit._data
    // Typically, user passes QuantumCircuit. We need to extract its _data.
    PyObject* py_data = PyObject_GetAttrString(py_circuit, "_data");
    if (!py_data) {
        // Fallback: assume the user passed _data directly
        PyErr_Clear();
        py_data = py_circuit;
        Py_INCREF(py_data);
    }

    QkCircuit* qc = qk_circuit_borrow_from_python(py_data);
    if (!qc) {
        Py_DECREF(py_data);
        return NULL; // Exception already set by qiskit
    }

    try {
        ::capnp::MallocMessageBuilder message;
        qiskit_to_jeff(qc, message);

        auto words = capnp::messageToFlatArray(message);
        auto bytes = words.asBytes();
        
        PyObject* result = PyBytes_FromStringAndSize(reinterpret_cast<const char*>(bytes.begin()), bytes.size());
        Py_DECREF(py_data);
        return result;
    } catch (const std::exception& e) {
        Py_DECREF(py_data);
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return NULL;
    }
}

static PyMethodDef JeffQiskitMethods[] = {
    {"jeff_to_qiskit", py_jeff_to_qiskit, METH_VARARGS, "Convert jeff binary to Qiskit QuantumCircuit."},
    {"qiskit_to_jeff", py_qiskit_to_jeff, METH_VARARGS, "Convert Qiskit QuantumCircuit to jeff binary."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef jeffqiskitmodule = {
    PyModuleDef_HEAD_INIT,
    "qiskit_jeff_py",
    "Python interface for bidirectional conversion between jeff and Qiskit C API",
    -1,
    JeffQiskitMethods
};

PyMODINIT_FUNC PyInit_qiskit_jeff_py(void) {
    return PyModule_Create(&jeffqiskitmodule);
}
