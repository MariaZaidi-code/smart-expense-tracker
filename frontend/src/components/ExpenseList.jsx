export default function ExpenseList({ items, onEdit, onDelete }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left border-b">
            <th className="py-2">Title</th>
            <th>Amount</th>
            <th>Category</th>
            <th>Date</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((x) => (
            <tr key={x.id} className="border-b">
              <td className="py-2">{x.title}</td>
              <td>${Number(x.amount).toFixed(2)}</td>
              <td>{x.category}</td>
              <td>{x.date?.slice(0, 10)}</td>
              <td className="space-x-2">
                <button onClick={() => onEdit(x)} className="text-blue-600">Edit</button>
                <button onClick={() => onDelete(x.id)} className="text-red-600">Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p className="text-gray-500 py-4">No expenses.</p>}
    </div>
  )
}
