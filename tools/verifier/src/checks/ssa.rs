use jeff::reader::Module;
use jeff::Direction;

use super::{Check, CheckError};

pub struct SsaCheck;

impl Check for SsaCheck {
    fn name(&self) -> &'static str {
        "ssa"
    }

    fn check(&self, module: &Module<'_>) -> Vec<CheckError> {
        let mut errors = vec![];

        for func in module.functions() {
            let func_name = func.name().to_string();
            let definition = match func {
                jeff::reader::Function::Definition(def) => def,
                jeff::reader::Function::Declaration(_) => continue,
            };

            let value_table = definition.values();
            let value_count = value_table.len();

            let body = definition.body();
            for (op_idx, op) in body.operations().enumerate() {
                for (io_idx, result) in op.inputs().enumerate() {
                    if let Err(e) = result {
                        errors.push(CheckError {
                            check_name: "ssa",
                            message: format!(
                                "Function '{func_name}', op[{op_idx}], input[{io_idx}]: {e}",
                            ),
                        });
                    }
                }
                for (io_idx, result) in op.outputs().enumerate() {
                    if let Err(e) = result {
                        errors.push(CheckError {
                            check_name: "ssa",
                            message: format!(
                                "Function '{func_name}', op[{op_idx}], output[{io_idx}]: {e}",
                            ),
                        });
                    }
                }

                for dir in [Direction::Incoming, Direction::Outgoing] {
                    for i in 0..op.boundary_count(dir) {
                        let val = match dir {
                            Direction::Incoming => op.input(i),
                            Direction::Outgoing => op.output(i),
                        };
                        match val {
                            None => {
                                errors.push(CheckError {
                                    check_name: "ssa",
                                    message: format!(
                                        "Function '{func_name}', op[{op_idx}], {dir}[{i}]: out of bounds (op has {} {dir}s)",
                                        op.boundary_count(dir),
                                    ),
                                });
                            }
                            Some(Ok(v)) if v.id() as usize >= value_count => {
                                errors.push(CheckError {
                                    check_name: "ssa",
                                    message: format!(
                                        "Function '{func_name}', op[{op_idx}], {dir}[{i}]: ValueId {} exceeds value table size {value_count}",
                                        v.id(),
                                    ),
                                });
                            }
                            _ => {}
                        }
                    }
                }
            }
        }

        errors
    }
}
