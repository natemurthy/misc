import { FC } from 'react'

const List: FC<{ data: string[] }> = ({ data }) => (
  <ul>
    {data.map(item => <li>{item}</li>)}
  </ul>
)

export default List
